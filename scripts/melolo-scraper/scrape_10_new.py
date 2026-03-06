#!/usr/bin/env python3
"""
VIDRAMA → R2 SCRAPER: 10 New Dramas (Full Data + Dedup)
========================================================
1. Discovers all dramas from vidrama.asia/api/melolo
2. Cross-references against R2 (slug check) AND DB (title check)
3. Picks first 10 truly new dramas  
4. Downloads: cover, metadata, ALL episodes (ep1 to last)
5. FFmpeg transcode: H.264 CRF28, AAC 128k, faststart
6. Uploads to R2 and registers in backend DB

Usage:
  python scrape_10_new.py
"""
import requests, json, time, os, re, sys, subprocess, tempfile, shutil, io
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import quote
import boto3

# ─── CONFIG ───

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stdout.reconfigure(line_buffering=True)

load_dotenv(Path(__file__).parent / '.env')

R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET = os.getenv("R2_BUCKET_NAME", "shortlovers")
R2_PUBLIC = "https://stream.shortlovers.id"
API_URL = "https://vidrama.asia/api/melolo"
BACKEND_URL = "http://localhost:3001/api"

TEMP_DIR = Path(tempfile.gettempdir()) / "vidrama_scrape"
TEMP_DIR.mkdir(exist_ok=True)

TARGET_COUNT = 10
API_TIMEOUT = 10
DOWNLOAD_TIMEOUT = 180


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return re.sub(r'-+', '-', text).strip('-')


def get_s3():
    return boto3.client("s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        region_name='auto'
    )


# ─── DEDUP CHECK ───

def get_r2_existing_slugs():
    """Get set of drama slugs already in R2."""
    print("  Checking R2 for existing dramas...", flush=True)
    s3 = get_s3()
    slugs = set()
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=R2_BUCKET, Prefix='melolo/', Delimiter='/'):
        for prefix in page.get('CommonPrefixes', []):
            slug = prefix['Prefix'].replace('melolo/', '').rstrip('/')
            slugs.add(slug)
    print(f"  R2 has {len(slugs)} drama folders", flush=True)
    return slugs


def get_db_existing_titles():
    """Get set of drama titles already in backend DB."""
    try:
        r = requests.get(f"{BACKEND_URL}/dramas?limit=500", timeout=5)
        if r.status_code == 200:
            data = r.json()
            items = data if isinstance(data, list) else data.get("dramas", [])
            titles = {d["title"] for d in items}
            print(f"  DB has {len(titles)} dramas", flush=True)
            return titles
    except Exception as e:
        print(f"  ⚠️ DB check failed: {e}", flush=True)
    return set()


# ─── DISCOVERY ───

def search_all_dramas():
    """Discover all Melolo dramas via search API."""
    print("\n  Searching vidrama.asia API...", flush=True)
    all_dramas = {}
    keywords = ["a", "e", "i", "o", "u", "s", "k", "p", "d", "m",
                "b", "c", "r", "n", "t", "l", "g", "h", "j", "w"]
    
    for kw in keywords:
        offset = 0
        while True:
            try:
                r = requests.get(
                    f"{API_URL}?action=search&keyword={kw}&limit=50&offset={offset}",
                    timeout=API_TIMEOUT
                )
                if r.status_code != 200:
                    break
                items = r.json().get("data", [])
                if not items:
                    break
                for item in items:
                    did = item.get("id", "")
                    if did and did not in all_dramas:
                        all_dramas[did] = item
                if len(items) < 50:
                    break
                offset += 50
                time.sleep(0.3)
            except requests.exceptions.Timeout:
                break
            except Exception:
                break
        
        sys.stdout.write(f"\r  Search '{kw}': {len(all_dramas)} unique dramas found    ")
        sys.stdout.flush()
        time.sleep(0.3)
    
    # Also grab trending
    try:
        r = requests.get(f"{API_URL}?action=all-trending&limit=100", timeout=API_TIMEOUT)
        if r.status_code == 200:
            for item in r.json().get("data", []):
                did = item.get("id", "")
                if did and did not in all_dramas:
                    all_dramas[did] = item
    except:
        pass
    
    print(f"\n  Total discovered: {len(all_dramas)} dramas\n", flush=True)
    return list(all_dramas.values())


# ─── FFMPEG ───

def transcode(input_path, output_path):
    """FFmpeg transcode: H.264 CRF28, AAC 128k, faststart."""
    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-c:v", "libx264", "-preset", "fast", "-crf", "28",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-ac", "2",
        "-movflags", "+faststart",
        str(output_path)
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 1000
    except:
        return False


# ─── PROCESS ONE DRAMA ───

def process_drama(drama, drama_num, total, s3):
    """Full pipeline for one drama: detail → download → transcode → R2 → DB."""
    drama_id = drama["id"]
    title = drama["title"]
    slug = slugify(title)
    
    print(f"\n{'═' * 60}", flush=True)
    print(f"  [{drama_num}/{total}] {title}", flush=True)
    print(f"  ID: {drama_id} | Slug: {slug}", flush=True)
    print(f"{'═' * 60}", flush=True)
    
    # 1) Get detail (episodes + metadata)
    try:
        r = requests.get(f"{API_URL}?action=detail&id={drama_id}", timeout=API_TIMEOUT)
        if r.status_code != 200:
            print(f"  ❌ Detail API failed: {r.status_code}", flush=True)
            return False
        detail = r.json().get("data", {})
    except Exception as e:
        print(f"  ❌ Detail error: {e}", flush=True)
        return False
    
    episodes = detail.get("episodes", [])
    total_eps = len(episodes)
    if total_eps == 0:
        print(f"  ❌ No episodes found!", flush=True)
        return False
    
    description = detail.get("description", drama.get("description", ""))
    genres = drama.get("genres", [])
    
    print(f"  📋 Title: {title}", flush=True)
    print(f"  📝 Description: {description[:80]}...", flush=True)
    print(f"  🎭 Genres: {genres if genres else 'N/A'}", flush=True)
    print(f"  📺 Episodes: {total_eps}", flush=True)
    
    # 2) Upload cover
    cover_url = drama.get("originalImage") or drama.get("image") or drama.get("poster", "")
    cover_ok = False
    if cover_url:
        try:
            resp = requests.get(cover_url, timeout=15)
            resp.raise_for_status()
            if len(resp.content) > 100:
                ct = resp.headers.get("content-type", "image/webp")
                ext = ".webp"
                if "jpeg" in ct or "jpg" in ct:
                    ext = ".jpg"
                elif "png" in ct:
                    ext = ".png"
                
                cover_key = f"melolo/{slug}/cover{ext}"
                s3.put_object(Bucket=R2_BUCKET, Key=cover_key, Body=resp.content, ContentType=ct)
                cover_ok = True
                print(f"  🖼️  Cover: ✅ ({len(resp.content)/1024:.0f}KB) → {cover_key}", flush=True)
        except Exception as e:
            print(f"  🖼️  Cover: ❌ {str(e)[:50]}", flush=True)
    
    if not cover_ok:
        # Try poster URL
        poster_url = drama.get("poster", "")
        if poster_url:
            try:
                resp = requests.get(poster_url, timeout=15)
                if resp.ok and len(resp.content) > 100:
                    s3.put_object(Bucket=R2_BUCKET, Key=f"melolo/{slug}/cover.webp",
                        Body=resp.content, ContentType="image/webp")
                    cover_ok = True
                    print(f"  🖼️  Cover (poster): ✅ ({len(resp.content)/1024:.0f}KB)", flush=True)
            except:
                pass
    
    # 3) Save metadata to R2
    metadata = {
        "title": title,
        "description": description,
        "genres": genres,
        "totalEpisodes": total_eps,
        "provider": "melolo",
        "seriesId": drama_id,
        "coverUrl": f"{R2_PUBLIC}/melolo/{slug}/cover.webp",
    }
    try:
        s3.put_object(
            Bucket=R2_BUCKET,
            Key=f"melolo/{slug}/metadata.json",
            Body=json.dumps(metadata, ensure_ascii=False, indent=2).encode('utf-8'),
            ContentType="application/json"
        )
        print(f"  📄 Metadata: ✅", flush=True)
    except Exception as e:
        print(f"  📄 Metadata: ❌ {e}", flush=True)
    
    # 4) Process ALL episodes
    drama_temp = TEMP_DIR / slug
    drama_temp.mkdir(exist_ok=True)
    
    uploaded_eps = []
    failed_eps = []
    
    for ep in episodes:
        ep_num = ep.get("episodeNumber", 0)
        if ep_num == 0:
            continue
        
        r2_key = f"melolo/{slug}/ep{ep_num:03d}.mp4"
        print(f"    Ep {ep_num:3}/{total_eps}:", end="", flush=True)
        
        # Check if already on R2
        try:
            s3.head_object(Bucket=R2_BUCKET, Key=r2_key)
            print(f" ⏭️  Already on R2", flush=True)
            uploaded_eps.append({
                "number": ep_num,
                "videoUrl": f"{R2_PUBLIC}/{r2_key}",
                "duration": ep.get("duration", 0),
            })
            continue
        except:
            pass  # Not on R2, proceed
        
        # Get stream URL
        try:
            sr = requests.get(
                f"{API_URL}?action=stream&id={drama_id}&episode={ep_num}",
                timeout=API_TIMEOUT
            )
            if sr.status_code != 200:
                print(f" ❌ Stream API {sr.status_code}", flush=True)
                failed_eps.append(ep_num)
                time.sleep(0.5)
                continue
            stream_data = sr.json().get("data", {})
        except Exception as e:
            print(f" ❌ Stream error: {str(e)[:40]}", flush=True)
            failed_eps.append(ep_num)
            time.sleep(0.5)
            continue
        
        proxy_url = stream_data.get("proxyUrl", "")
        if not proxy_url:
            print(f" ❌ No proxy URL", flush=True)
            failed_eps.append(ep_num)
            time.sleep(0.5)
            continue
        
        # Download raw MP4
        raw_path = drama_temp / f"raw_ep{ep_num:03d}.mp4"
        out_path = drama_temp / f"ep{ep_num:03d}.mp4"
        
        full_url = f"https://vidrama.asia{proxy_url}" if proxy_url.startswith("/") else proxy_url
        print(f" DL", end="", flush=True)
        
        try:
            resp = requests.get(full_url, timeout=DOWNLOAD_TIMEOUT, stream=True)
            resp.raise_for_status()
            total_bytes = 0
            with open(raw_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=1024 * 1024):
                    f.write(chunk)
                    total_bytes += len(chunk)
            
            if total_bytes < 1000:
                print(f" ❌ Too small ({total_bytes}B)", flush=True)
                failed_eps.append(ep_num)
                raw_path.unlink(missing_ok=True)
                continue
            
            raw_mb = total_bytes / 1024 / 1024
            print(f"({raw_mb:.1f}MB)", end="", flush=True)
        except Exception as e:
            print(f" ❌ DL error: {str(e)[:40]}", flush=True)
            failed_eps.append(ep_num)
            raw_path.unlink(missing_ok=True)
            time.sleep(0.5)
            continue
        
        # FFmpeg transcode
        print(f" → FFmpeg", end="", flush=True)
        if transcode(raw_path, out_path):
            out_mb = out_path.stat().st_size / 1024 / 1024
            saved_pct = (1 - out_mb / raw_mb) * 100 if raw_mb > 0 else 0
            print(f"({out_mb:.1f}MB,{saved_pct:+.0f}%)", end="", flush=True)
            upload_path = out_path
        else:
            print(f"(raw fallback)", end="", flush=True)
            upload_path = raw_path
        
        # Upload to R2
        print(f" → R2", end="", flush=True)
        try:
            s3.upload_file(str(upload_path), R2_BUCKET, r2_key,
                ExtraArgs={"ContentType": "video/mp4"})
            final_mb = upload_path.stat().st_size / 1024 / 1024
            print(f" ✅ ({final_mb:.1f}MB)", flush=True)
            uploaded_eps.append({
                "number": ep_num,
                "videoUrl": f"{R2_PUBLIC}/{r2_key}",
                "duration": ep.get("duration", 0),
            })
        except Exception as e:
            print(f" ❌ R2: {str(e)[:40]}", flush=True)
            failed_eps.append(ep_num)
        
        # Cleanup temp
        raw_path.unlink(missing_ok=True)
        out_path.unlink(missing_ok=True)
        
        time.sleep(0.5)
    
    # Cleanup drama temp dir
    shutil.rmtree(drama_temp, ignore_errors=True)
    
    # 5) Register in backend DB
    print(f"\n  📊 Result: {len(uploaded_eps)}/{total_eps} episodes uploaded", flush=True)
    if failed_eps:
        print(f"  ⚠️  Failed episodes: {failed_eps}", flush=True)
    
    if uploaded_eps:
        try:
            # Determine cover extension  
            cover_ext = ".webp"
            for ext in [".jpg", ".png", ".webp"]:
                try:
                    s3.head_object(Bucket=R2_BUCKET, Key=f"melolo/{slug}/cover{ext}")
                    cover_ext = ext
                    break
                except:
                    continue
            
            drama_payload = {
                "title": title,
                "description": description,
                "coverUrl": f"{R2_PUBLIC}/melolo/{slug}/cover{cover_ext}",
                "provider": "melolo",
                "totalEpisodes": len(uploaded_eps),
                "isActive": True,
            }
            r = requests.post(f"{BACKEND_URL}/dramas", json=drama_payload, timeout=10)
            if r.status_code in [200, 201]:
                drama_db_id = r.json().get("id")
                ep_ok = 0
                for ep in sorted(uploaded_eps, key=lambda x: x["number"]):
                    er = requests.post(f"{BACKEND_URL}/episodes", json={
                        "dramaId": drama_db_id,
                        "episodeNumber": ep["number"],
                        "videoUrl": ep["videoUrl"],
                        "duration": ep.get("duration", 0),
                    }, timeout=10)
                    if er.status_code in [200, 201]:
                        ep_ok += 1
                print(f"  🗄️  DB: ✅ Drama + {ep_ok} episodes registered", flush=True)
            else:
                print(f"  🗄️  DB: ❌ {r.status_code} {r.text[:80]}", flush=True)
        except Exception as e:
            print(f"  🗄️  DB: ❌ {e}", flush=True)
    
    return len(uploaded_eps) > 0


# ─── MAIN ───

def main():
    print("═" * 60, flush=True)
    print("  VIDRAMA → R2 SCRAPER (10 New Dramas, Full Data)", flush=True)
    print("═" * 60, flush=True)
    
    # 1) Check R2 and DB for existing content
    r2_slugs = get_r2_existing_slugs()
    db_titles = get_db_existing_titles()
    
    # 2) Discover all dramas from vidrama.asia
    all_dramas = search_all_dramas()
    
    # 3) Filter out existing dramas (check BOTH slug in R2 AND title in DB)
    new_dramas = []
    for d in all_dramas:
        title = d["title"]
        slug = slugify(title)
        in_r2 = slug in r2_slugs
        in_db = title in db_titles
        if not in_r2 and not in_db:
            new_dramas.append(d)
    
    print(f"\n  ═══ DEDUP RESULT ═══", flush=True)
    print(f"  Discovered: {len(all_dramas)}", flush=True)
    print(f"  Already in R2: {len([d for d in all_dramas if slugify(d['title']) in r2_slugs])}", flush=True)
    print(f"  Already in DB: {len([d for d in all_dramas if d['title'] in db_titles])}", flush=True)
    print(f"  Truly NEW: {len(new_dramas)}", flush=True)
    
    if not new_dramas:
        print("\n  ✅ All dramas already exist! Nothing to scrape.", flush=True)
        return
    
    # 4) Pick first N new dramas
    target = min(TARGET_COUNT, len(new_dramas))
    selected = new_dramas[:target]
    
    print(f"\n  Will scrape {target} new dramas:", flush=True)
    for i, d in enumerate(selected, 1):
        print(f"    {i:2}. {d['title']}", flush=True)
    
    # 5) Scrape each drama
    s3 = get_s3()
    results = {"ok": 0, "fail": 0, "total_eps": 0}
    start_time = time.time()
    
    for i, drama in enumerate(selected, 1):
        ok = process_drama(drama, i, target, s3)
        if ok:
            results["ok"] += 1
        else:
            results["fail"] += 1
        
        # Brief cooldown between dramas
        if i < target:
            time.sleep(2)
    
    elapsed = time.time() - start_time
    
    print(f"\n{'═' * 60}", flush=True)
    print(f"  SCRAPING COMPLETE!", flush=True)
    print(f"{'═' * 60}", flush=True)
    print(f"  ✅ Success: {results['ok']} dramas", flush=True)
    print(f"  ❌ Failed:  {results['fail']} dramas", flush=True)
    print(f"  ⏱️  Time:   {elapsed/60:.1f} minutes", flush=True)
    print(f"{'═' * 60}", flush=True)


if __name__ == "__main__":
    main()
