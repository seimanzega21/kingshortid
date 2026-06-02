#!/usr/bin/env python3
"""
VIDRAMA MICRODRAMA INGESTION PIPELINE v5 - REAL-TIME & LINEAR
==============================================================
Optimizations & Features:
  - Linear processing: Processes episodes one by one sequentially (EP_WORKERS = 1) to avoid target IP blocks.
  - Initial Drama Registration: Registers the drama in the database first with "isActive: False" (Pending)
    so it immediately shows in the Admin panel.
  - Real-time Episode Registration: Registers each episode in the database immediately after upload to R2,
    allowing live progress tracking from the Admin panel.
  - Resilient Ingestion: Scans database for already registered episodes and skips them dynamically,
    making it safe to resume crashed sessions without double processing.
  - Automatic 720p/540p faststart compression and R2 upload.
"""
import requests, json, time, os, re, sys, subprocess, shutil, boto3
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.stdout.reconfigure(encoding="utf-8")

# ──────────────────── CONFIG ────────────────────
API_LIST_URL  = "https://vidrama.asia/api/microdrama?action=list&lang=id"
BACKEND_URL   = "https://api.shortlovers.id/api"
R2_PUBLIC     = "https://stream.shortlovers.id"
R2_BUCKET     = os.getenv("R2_BUCKET_NAME") or "shortlovers"
R2_PREFIX     = "dramas/microdrama"
TEMP_DIR      = Path("/tmp/microdrama_mp4_v5") if os.name != 'nt' else Path("C:/tmp/microdrama_mp4_v5")
LOG_FILE      = Path(__file__).parent / "microdrama_mp4_v5.log"
DRAMA_LIMIT   = 300
QUALITY_PREF  = ["720P", "540P", "480P", "360P"]

# Auth Header for admin endpoints
ADMIN_KEY = os.getenv("ADMIN_API_KEY") or "00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14"
ADMIN_HDR = {"x-admin-key": ADMIN_KEY, "Content-Type": "application/json"}

_log_fh = open(LOG_FILE, "a", encoding="utf-8")

def log(msg="", end="\n"):
    try:
        print(msg, end=end, flush=True)
    except:
        pass
    _log_fh.write(msg + end)
    _log_fh.flush()

# ──────────────────── HELPERS ────────────────────
def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")

_s3 = None
def get_s3():
    global _s3
    if _s3 is None:
        _s3 = boto3.client("s3",
            endpoint_url=os.getenv("R2_ENDPOINT"),
            aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
            region_name="auto",
        )
    return _s3

# ──────────────────── DISCOVERY ────────────────────
def discover_dramas(target=300) -> list:
    log("[1] Discovering Indonesian MicroDrama dramas...")
    try:
        r = requests.get(f"{API_LIST_URL}&limit={target}", timeout=30)
        if r.status_code == 200:
            data = r.json()
            dramas = data.get("dramas", [])
            log(f"    Discovered: {len(dramas)} dramas")
            return dramas
    except Exception as e:
        log(f"    Error: {e}")
    return []

# ──────────────────── DATABASE CHECKS ────────────────────
def get_supabase_dramas() -> list:
    log("[2] Fetching Supabase registered dramas...")
    try:
        # includeInactive=true is important to fetch pending ones
        r = requests.get(f"{BACKEND_URL}/dramas?limit=1000&includeInactive=true", headers=ADMIN_HDR, timeout=15)
        data = r.json()
        items = data if isinstance(data, list) else data.get("dramas", [])
        log(f"    Supabase: {len(items)} registered dramas found")
        return items
    except Exception as e:
        log(f"    Supabase fetch error: {e}")
        return []

def get_existing_episodes(drama_id: str) -> set:
    try:
        r = requests.get(f"{BACKEND_URL}/dramas/{drama_id}?includeInactive=true", headers=ADMIN_HDR, timeout=15)
        if r.status_code == 200:
            data = r.json()
            eps = data.get("episodes", [])
            # Only consider complete if it has both 720p (videoUrl) and 540p (videoUrl540p)
            completed_eps = {
                e["episodeNumber"] for e in eps 
                if e.get("videoUrl") and e.get("videoUrl540p")
            }
            return completed_eps
    except Exception as e:
        log(f"    Failed to get existing episodes for drama {drama_id}: {e}")
    return set()

# ──────────────────── EPISODE DATA ────────────────────
def fetch_episodes(drama_id: str) -> list:
    url = f"https://vidrama.asia/api/microdrama?action=detail&id={drama_id}&lang=id"
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            data = r.json()
            return data.get("episodes", [])
    except Exception as e:
        log(f"  Episode fetch error: {e}")
    return []

def get_best_url(videos: list) -> str | None:
    qmap = {v.get("quality", ""): v.get("url", "") for v in videos}
    for q in QUALITY_PREF:
        if qmap.get(q): return qmap[q]
    for v in videos:
        if v.get("url"): return v["url"]
    return None

# ──────────────────── VIDEO PROCESSING ────────────────────
def download_mp4(url: str, dest: Path) -> bool:
    for attempt in range(3):
        try:
            resp = requests.get(url, timeout=120, stream=True)
            resp.raise_for_status()
            total = 0
            with open(dest, "wb") as f:
                for chunk in resp.iter_content(chunk_size=2 * 1024 * 1024):
                    f.write(chunk)
                    total += len(chunk)
            if total > 5000:
                return True
        except Exception as e:
            if attempt < 2:
                time.sleep(2)
            else:
                log(f" DLerr:{str(e)[:30]}", end="")
    return False

def compress_variants(input_mp4: Path, base_output: str, temp_dir: Path) -> tuple[Path|None, Path|None]:
    out_720 = temp_dir / f"{base_output}.mp4"
    out_540 = temp_dir / f"{base_output}_540p.mp4"
    
    cmd_720 = [
        "ffmpeg", "-y", "-i", str(input_mp4),
        "-c:v", "libx264", "-preset", "faster", "-crf", "28",
        "-maxrate", "1200k", "-bufsize", "2400k",
        "-movflags", "+faststart", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "96k", "-ac", "2",
        str(out_720)
    ]
    
    cmd_540 = [
        "ffmpeg", "-y", "-i", str(input_mp4),
        "-vf", "scale=-2:540",
        "-c:v", "libx264", "-preset", "faster", "-crf", "28",
        "-maxrate", "800k", "-bufsize", "1600k",
        "-movflags", "+faststart", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "96k", "-ac", "2",
        str(out_540)
    ]
    
    try:
        res1 = subprocess.run(cmd_720, capture_output=True, timeout=300)
        res2 = subprocess.run(cmd_540, capture_output=True, timeout=300)
        
        ok1 = res1.returncode == 0 and out_720.exists()
        ok2 = res2.returncode == 0 and out_540.exists()
        
        log(f" FF:{res1.returncode},{res2.returncode}", end="")
        return (out_720 if ok1 else None, out_540 if ok2 else None)
    except Exception as e:
        log(f" FFexe:{str(e)[:50]}")
        return None, None

def upload_mp4(mp4_file: Path, r2_key: str) -> str | None:
    if not mp4_file.exists(): return None
    get_s3().upload_file(str(mp4_file), R2_BUCKET, r2_key,
                         ExtraArgs={"ContentType": "video/mp4"})
    return f"{R2_PUBLIC}/{r2_key}"

def upload_cover(cover_url: str, slug: str) -> str | None:
    if not cover_url: return None
    try:
        resp = requests.get(cover_url, timeout=15)
        resp.raise_for_status()
        if len(resp.content) < 100: return None
        ctype = resp.headers.get("content-type", "image/jpeg")
        ext = "webp" if "webp" in ctype else "png" if "png" in ctype else "jpg"
        cover_key = f"{R2_PREFIX}/{slug}/cover.{ext}"
        get_s3().put_object(Bucket=R2_BUCKET,
                            Key=cover_key,
                            Body=resp.content,
                            ContentType=ctype)
        return f"{R2_PUBLIC}/{cover_key}"
    except:
        return None

# ──────────────────── D1 REGISTRATION ────────────────────
def get_or_create_drama(drama: dict, slug: str, cover_url: str) -> str | None:
    title = drama.get("title", slug)
    cover = cover_url if cover_url else f"{R2_PUBLIC}/{R2_PREFIX}/{slug}/cover.jpg"
    
    # Heuristic genres based on keywords
    genres = ["Drama", "Romance"]
    desc_lower = drama.get("description", "").lower()
    title_lower = title.lower()
    if any(x in desc_lower or x in title_lower for x in ["cinta", "romantis", "nikah", "istri", "suami", "sayang", "kekasih"]):
        genres.append("Romantis")
    if any(x in desc_lower or x in title_lower for x in ["sakti", "tombak", "pedang", "naga", "pendekar", "dewa", "warisan", "tanding", "dendam"]):
        genres.append("Aksi")
        genres.append("Fantasi")
        
    try:
        resp = requests.post(f"{BACKEND_URL}/dramas", json={
            "title": title,
            "description": drama.get("description", "No description available"),
            "cover": cover,
            "provider": "microdrama",
            "genres": list(set(genres)),
            "totalEpisodes": drama.get("episodes", 0),
            "isActive": False, # Always registered as Pending
        }, headers=ADMIN_HDR, timeout=15)
        
        if resp.status_code in [200, 201]:
            did = resp.json().get("id")
            return did
        else:
            log(f"  Drama register FAIL: {resp.status_code} {resp.text[:80]}")
    except Exception as e:
        log(f"  Register drama error: {e}")
    return None

def register_episode(drama_id: str, ep_number: int, url_720: str, url_540: str) -> bool:
    try:
        resp = requests.post(f"{BACKEND_URL}/episodes", json={
            "dramaId": drama_id,
            "episodeNumber": ep_number,
            "videoUrl": url_720,
            "videoUrl540p": url_540,
            "duration": 0,
        }, headers=ADMIN_HDR, timeout=10)
        return resp.status_code in [200, 201]
    except Exception as e:
        log(f"  Episode DB register error: {e}")
    return False

# ──────────────────── MAIN ────────────────────
def main():
    limit = DRAMA_LIMIT
    start = 0
    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        if idx + 1 < len(sys.argv):
            limit = int(sys.argv[idx + 1])
    if "--start" in sys.argv:
        idx = sys.argv.index("--start")
        if idx + 1 < len(sys.argv):
            start = int(sys.argv[idx + 1])

    log("=" * 60)
    log("  VIDRAMA MICRODRAMA SCRAPER v5 (LINEAR & REAL-TIME)")
    log(f"  Limit: {limit} | Start: {start}")
    log("=" * 60)

    discovered      = discover_dramas(target=limit + 150)
    supabase_dramas = get_supabase_dramas()
    
    # Build maps of existing titles for filtering
    registered_titles = {d["title"].lower().strip(): d for d in supabase_dramas}

    new_to_process = []
    for d in discovered:
        title = d.get("title", "").lower().strip()
        
        # Check if already registered
        if title in registered_titles:
            existing_drama = registered_titles[title]
            # If the drama has 0 episodes in DB or is missing episodes, we process it to complete it
            # Otherwise we skip it
            if existing_drama.get("totalEpisodes", 0) > 2:
                # We can do a quick check of how many eps exist in DB
                # But for safety, let's process it (the episode process will skip matching R2 anyway)
                pass
            
        new_to_process.append(d)
        if len(new_to_process) >= limit:
            break

    if not new_to_process:
        log("  No new dramas to process!"); return

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    stats = {"ok": 0, "fail": 0, "eps_registered": 0}

    for i, drama in enumerate(new_to_process, 1):
        drama_id_provider = str(drama["id"])
        title = drama.get("title", "Untitled")
        slug = slugify(title)
        
        log(f"\n{'_'*60}")
        log(f"  [{i}/{len(new_to_process)}] Processing: {title}")
        log(f"  Slug: {slug} | Provider ID: {drama_id_provider}")

        # 1. Upload cover image to R2 first
        cover_url = upload_cover(drama.get("cover", ""), slug)

        # 2. Register/Get drama ID in Supabase as Inactive/Pending
        drama_id = get_or_create_drama(drama, slug, cover_url)
        if not drama_id:
            log("  [ERROR] Failed to get or register drama in DB. Skipping.")
            stats["fail"] += 1
            continue
            
        log(f"  Supabase Drama ID: {drama_id}")

        # 3. Get existing episodes in DB to avoid processing them again
        existing_eps = get_existing_episodes(drama_id)
        log(f"  Episodes already in DB (with 720p & 540p): {len(existing_eps)}")

        # 4. Fetch episode list from Provider API
        episodes_provider = fetch_episodes(drama_id_provider)
        if not episodes_provider:
            log("  [ERROR] No episodes found in Provider API. Skipping.")
            stats["fail"] += 1
            continue

        total_eps = len(episodes_provider)
        log(f"  Total episodes from provider: {total_eps}")

        # Sort episodes by index
        sorted_eps = sorted(episodes_provider, key=lambda e: e.get("index", 0))

        drama_temp = TEMP_DIR / slug
        drama_temp.mkdir(parents=True, exist_ok=True)

        successful_eps = 0
        
        # 5. Process episodes LINEARLY (One by one)
        for ep in sorted_eps:
            ep_num = ep.get("index", 0)
            if ep_num == 0: continue

            # Bypass if already registered in DB with both qualities
            if ep_num in existing_eps:
                successful_eps += 1
                continue

            videos = ep.get("videos", [])
            video_url = get_best_url(videos)
            if not video_url:
                log(f"    Ep {ep_num:3}/{total_eps}: SKIP no URL")
                continue

            r2_ep_key = f"{R2_PREFIX}/{slug}/ep{ep_num:03d}.mp4"
            r2_540_key = r2_ep_key.replace(".mp4", "_540p.mp4")

            log(f"    Ep {ep_num:3}/{total_eps}:", end="")

            # Check R2 first (just in case it's in R2 but failed database register)
            url_720 = None
            url_540 = None
            try:
                get_s3().head_object(Bucket=R2_BUCKET, Key=r2_ep_key)
                get_s3().head_object(Bucket=R2_BUCKET, Key=r2_540_key)
                # Found in R2! Skip conversion
                url_720 = f"{R2_PUBLIC}/{r2_ep_key}"
                url_540 = f"{R2_PUBLIC}/{r2_540_key}"
                log(" Already in R2", end="")
            except:
                # Downloader & Compressor
                raw = drama_temp / f"raw_ep{ep_num:03d}.mp4"
                if download_mp4(video_url, raw):
                    mb = raw.stat().st_size / 1024 / 1024
                    log(f" DL({mb:.1f}MB)", end="")
                    
                    c720, c540 = compress_variants(raw, f"opt_ep{ep_num:03d}", drama_temp)
                    if c720:
                        mb_720 = c720.stat().st_size / 1024 / 1024
                        mb_540 = c540.stat().st_size / 1024 / 1024 if c540 else 0
                        log(f" COMP(720={mb_720:.1f}MB|540={mb_540:.1f}MB)", end="")
                        
                        url_720 = upload_mp4(c720, r2_ep_key)
                        if c540:
                            url_540 = upload_mp4(c540, r2_540_key)
                            
                        # Cleanup temp episode files immediately
                        c720.unlink(missing_ok=True)
                        if c540: c540.unlink(missing_ok=True)
                    else:
                        log(" COMP FAIL", end="")
                    raw.unlink(missing_ok=True)
                else:
                    log(" DL FAIL", end="")

            # Register in Database real-time
            if url_720 and url_540:
                if register_episode(drama_id, ep_num, url_720, url_540):
                    log(" -> DB REGISTERED OK")
                    successful_eps += 1
                    stats["eps_registered"] += 1
                else:
                    log(" -> DB REGISTER FAIL")
            else:
                log(" -> PROCESS FAIL")

            # Be nice to target servers, sleep 1s between episodes
            time.sleep(1.0)

        # Cleanup drama folder
        shutil.rmtree(drama_temp, ignore_errors=True)

        if successful_eps > 2:
            # Update drama total episodes in DB
            try:
                requests.patch(f"{BACKEND_URL}/dramas/{drama_id}", json={
                    "totalEpisodes": successful_eps
                }, headers=ADMIN_HDR, timeout=10)
            except: pass
            
            log(f"  Drama completed: {successful_eps}/{total_eps} episodes registered.")
            stats["ok"] += 1
        else:
            log(f"  Drama failed or too few episodes: {successful_eps}/{total_eps}")
            stats["fail"] += 1

        time.sleep(1.5) # pause between dramas

    shutil.rmtree(TEMP_DIR, ignore_errors=True)

    log(f"\n{'='*60}")
    log(f"  ALL DONE: {stats['ok']} dramas fully processed, {stats['eps_registered']} episodes registered")
    log(f"  Failed: {stats['fail']}")
    log(f"{'='*60}")

if __name__ == "__main__":
    main()
