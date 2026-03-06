#!/usr/bin/env python3
"""
FAST VIDRAMA SCRAPER - Quick 10-drama batch
============================================
Skips full discovery. Uses fast keyword search to find new dramas,
then scrapes them: metadata + cover + MP4 (FFmpeg) → R2 + backend.
"""
import requests, json, time, os, re, sys, subprocess, tempfile, shutil
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Config
R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET = os.getenv("R2_BUCKET_NAME")
R2_PUBLIC = "https://stream.shortlovers.id"
API_URL = "https://vidrama.asia/api/melolo"
BACKEND_URL = "http://localhost:3001/api"
TEMP_DIR = Path(tempfile.gettempdir()) / "vidrama_scrape"
TEMP_DIR.mkdir(exist_ok=True)

_s3 = None
def get_s3():
    global _s3
    if _s3 is None:
        import boto3
        _s3 = boto3.client("s3", endpoint_url=R2_ENDPOINT,
            aws_access_key_id=R2_ACCESS_KEY, aws_secret_access_key=R2_SECRET_KEY)
    return _s3

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return re.sub(r'-+', '-', text).strip('-')

# ─── FAST DISCOVERY ──────────────────────────────────────────

def quick_discover():
    """Fast discovery using subset of keywords."""
    print("  Discovering dramas (fast mode)...", flush=True)
    all_dramas = {}
    keywords = ["a", "e", "i", "o", "u", "s", "k", "p", "b", "c",
                "d", "m", "r", "n", "t", "l", "g", "h", "j", "w"]

    for kw in keywords:
        try:
            r = requests.get(
                f"{API_URL}?action=search&keyword={kw}&limit=50&offset=0",
                timeout=15
            )
            if r.status_code == 200:
                for d in r.json().get("data", []):
                    did = d.get("id", "")
                    if did and did not in all_dramas:
                        all_dramas[did] = d
            print(f"    '{kw}' → {len(all_dramas)} unique", flush=True)
            time.sleep(0.3)
        except Exception as e:
            print(f"    '{kw}' ERROR: {str(e)[:40]}", flush=True)
            time.sleep(1)

    print(f"  Found: {len(all_dramas)} total dramas\n", flush=True)
    return list(all_dramas.values())

def get_existing_titles():
    try:
        r = requests.get(f"{BACKEND_URL}/dramas?limit=500", timeout=5)
        if r.status_code == 200:
            data = r.json()
            items = data if isinstance(data, list) else data.get("dramas", [])
            return {d["title"] for d in items}
    except:
        pass
    return set()

# ─── FFMPEG + DOWNLOAD + UPLOAD ──────────────────────────────

def transcode(input_path, output_path):
    cmd = ["ffmpeg", "-y", "-i", str(input_path),
           "-c:v", "libx264", "-preset", "fast", "-crf", "28",
           "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "128k", "-ac", "2",
           "-movflags", "+faststart", str(output_path)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return r.returncode == 0 and output_path.exists() and output_path.stat().st_size > 1000
    except:
        return False

def download_mp4(proxy_url, output_path):
    full_url = f"https://vidrama.asia{proxy_url}" if proxy_url.startswith("/") else proxy_url
    try:
        resp = requests.get(full_url, timeout=120, stream=True)
        resp.raise_for_status()
        total = 0
        with open(output_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=1024*1024):
                f.write(chunk)
                total += len(chunk)
        return total > 1000
    except Exception as e:
        print(f"        DL error: {str(e)[:50]}")
        return False

def upload_to_r2(file_path, r2_key):
    try:
        ct = "video/mp4" if r2_key.endswith(".mp4") else "image/jpeg"
        get_s3().upload_file(str(file_path), R2_BUCKET, r2_key, ExtraArgs={"ContentType": ct})
        return True
    except Exception as e:
        print(f"        R2 error: {str(e)[:50]}")
        return False

def upload_cover(url, r2_key):
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        if len(resp.content) < 100:
            return False
        ct = resp.headers.get("content-type", "image/jpeg")
        # Determine file extension from content-type
        ext = "jpg" if "jpeg" in ct or "jpg" in ct else "webp" if "webp" in ct else "jpg"
        # Update r2_key extension if needed
        if not r2_key.endswith(f".{ext}"):
            r2_key = r2_key.rsplit(".", 1)[0] + f".{ext}"
        get_s3().put_object(Bucket=R2_BUCKET, Key=r2_key, Body=resp.content, ContentType=ct)
        return r2_key
    except Exception as e:
        print(f"        Cover error: {str(e)[:50]}")
        return False

def register_drama(info, slug, uploaded_eps, cover_key):
    try:
        cover_url = f"{R2_PUBLIC}/{cover_key}" if cover_key else ""
        genres = info.get("genres", [])
        if isinstance(genres, str):
            genres = [g.strip() for g in genres.split(",")]
        
        payload = {
            "title": info["title"],
            "description": info.get("description", info.get("desc", "")),
            "coverUrl": cover_url,
            "provider": "melolo",
            "totalEpisodes": len(uploaded_eps),
            "genres": genres,
            "isActive": True,
        }
        r = requests.post(f"{BACKEND_URL}/dramas", json=payload, timeout=10)
        if r.status_code not in [200, 201]:
            print(f"    ⚠️ Drama API: {r.status_code} {r.text[:80]}")
            return False
        drama_id = r.json().get("id")
        for ep in uploaded_eps:
            requests.post(f"{BACKEND_URL}/episodes", json={
                "dramaId": drama_id,
                "episodeNumber": ep["number"],
                "videoUrl": ep["videoUrl"],
                "duration": ep.get("duration", 0),
            }, timeout=10)
        print(f"    ✅ Registered: {len(uploaded_eps)} episodes")
        return True
    except Exception as e:
        print(f"    ⚠️ Backend: {e}")
        return False

# ─── PROCESS DRAMA ───────────────────────────────────────────

def process_drama(drama, slug):
    drama_id = drama["id"]
    title = drama["title"]

    # Get detail + episodes
    try:
        r = requests.get(f"{API_URL}?action=detail&id={drama_id}", timeout=15)
        if r.status_code != 200:
            print(f"  ❌ Detail failed: {r.status_code}")
            return None
        detail = r.json().get("data", {})
    except Exception as e:
        print(f"  ❌ Detail error: {e}")
        return None

    episodes = detail.get("episodes", [])
    if not episodes:
        print(f"  ❌ No episodes")
        return None

    # Merge detail into drama info
    drama["description"] = detail.get("description", detail.get("desc", drama.get("description", "")))
    drama["genres"] = detail.get("genres", drama.get("genres", []))

    total_eps = len(episodes)
    print(f"  Episodes: {total_eps}", flush=True)

    # Upload cover
    cover_url = drama.get("image") or drama.get("poster", "")
    cover_key = None
    if cover_url:
        cover_key = upload_cover(cover_url, f"melolo/{slug}/cover.jpg")
        print(f"  Cover: {'✅' if cover_key else '❌'}", flush=True)

    # Process episodes
    uploaded = []
    drama_temp = TEMP_DIR / slug
    drama_temp.mkdir(exist_ok=True)

    for ep in episodes:
        ep_num = ep.get("episodeNumber", 0)
        if ep_num == 0:
            continue

        r2_key = f"melolo/{slug}/ep{ep_num:03d}.mp4"
        print(f"    Ep {ep_num:3}/{total_eps}:", end="", flush=True)

        # Get stream URL
        try:
            sr = requests.get(
                f"{API_URL}?action=stream&id={drama_id}&episode={ep_num}",
                timeout=15
            )
            if sr.status_code != 200:
                print(f" ❌ Stream {sr.status_code}")
                time.sleep(0.5)
                continue
            stream_data = sr.json().get("data", {})
        except Exception as e:
            print(f" ❌ Stream: {str(e)[:40]}")
            time.sleep(0.5)
            continue

        proxy_url = stream_data.get("proxyUrl", "")
        if not proxy_url:
            print(f" ❌ No proxy")
            time.sleep(0.5)
            continue

        # Download
        raw_path = drama_temp / f"raw_ep{ep_num:03d}.mp4"
        out_path = drama_temp / f"ep{ep_num:03d}.mp4"

        print(f" DL", end="", flush=True)
        if not download_mp4(proxy_url, raw_path):
            print(f" ❌ DL fail")
            time.sleep(0.5)
            continue

        raw_mb = raw_path.stat().st_size / 1024 / 1024
        print(f"({raw_mb:.1f}MB)", end="", flush=True)

        # Transcode
        print(f" → FFmpeg", end="", flush=True)
        if not transcode(raw_path, out_path):
            print(f" (using raw)", end="", flush=True)
            out_path = raw_path

        out_mb = out_path.stat().st_size / 1024 / 1024
        savings = (1 - out_mb / raw_mb) * 100 if raw_mb > 0 else 0
        print(f"({out_mb:.1f}MB, {savings:+.0f}%)", end="", flush=True)

        # Upload
        print(f" → R2", end="", flush=True)
        if upload_to_r2(out_path, r2_key):
            print(f" ✅")
            uploaded.append({
                "number": ep_num,
                "videoUrl": f"{R2_PUBLIC}/{r2_key}",
                "duration": ep.get("duration", 0),
            })
        else:
            print(f" ❌ Upload fail")

        # Cleanup temp
        raw_path.unlink(missing_ok=True)
        if out_path != raw_path:
            out_path.unlink(missing_ok=True)

        time.sleep(0.5)

    shutil.rmtree(drama_temp, ignore_errors=True)
    return uploaded, cover_key

# ─── MAIN ────────────────────────────────────────────────────

def main():
    limit = 10
    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        if idx + 1 < len(sys.argv):
            limit = int(sys.argv[idx + 1])

    print("=" * 60)
    print("  FAST VIDRAMA SCRAPER")
    print(f"  Target: {limit} new dramas")
    print("=" * 60)

    dramas = quick_discover()
    existing = get_existing_titles()
    new_dramas = [d for d in dramas if d["title"] not in existing]

    print(f"  DB has: {len(existing)} dramas")
    print(f"  New available: {len(new_dramas)}")

    if not new_dramas:
        print("  Nothing new!")
        return

    new_dramas = new_dramas[:limit]
    print(f"  Will scrape: {limit}\n")

    stats = {"ok": 0, "fail": 0, "eps": 0}
    for i, drama in enumerate(new_dramas, 1):
        slug = slugify(drama["title"])
        print(f"\n{'─' * 60}")
        print(f"  [{i}/{len(new_dramas)}] {drama['title']}")
        print(f"  Slug: {slug}")

        result = process_drama(drama, slug)

        if result:
            uploaded, cover_key = result
            if uploaded and register_drama(drama, slug, uploaded, cover_key):
                stats["ok"] += 1
                stats["eps"] += len(uploaded)
            else:
                stats["fail"] += 1
        else:
            stats["fail"] += 1

        time.sleep(1)

    print(f"\n{'=' * 60}")
    print(f"  DONE: {stats['ok']} dramas, {stats['eps']} episodes")
    print(f"  Failed: {stats['fail']}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
