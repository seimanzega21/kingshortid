#!/usr/bin/env python3
"""
VIDRAMA → R2 DIRECT MP4 SCRAPER (with FFmpeg transcoding)
==========================================================
Scrapes dramas from vidrama.asia/provider/melolo API,
downloads MP4, transcodes via ffmpeg, and uploads to R2.

Pipeline per episode:
  1. Stream API → get video proxy URL
  2. Download raw MP4 from proxy
  3. FFmpeg transcode: H.264 CRF28, AAC 128k, faststart
  4. Upload transcoded MP4 to R2
  5. Cleanup temp files

Usage:
  python vidrama_to_r2.py                       # Discovery only
  python vidrama_to_r2.py --scrape              # Full scrape + R2 upload
  python vidrama_to_r2.py --scrape --limit 3    # Scrape first 3 new dramas
  python vidrama_to_r2.py --scrape --skip-existing  # Skip already uploaded eps
"""
import requests, json, time, os, re, sys, subprocess, tempfile, shutil
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import quote

load_dotenv()

# Internal file logging for monitoring progress
LOG_FILE = Path(__file__).parent / "vidrama_scrape.log"
_log_fh = open(LOG_FILE, "w", encoding="utf-8")

def log(msg="", end="\n", flush=True):
    """Print to both stdout and log file."""
    print(msg, end=end, flush=flush)
    _log_fh.write(msg + end)
    if flush:
        _log_fh.flush()


# R2 config
R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET = os.getenv("R2_BUCKET_NAME")
R2_PUBLIC = "https://stream.shortlovers.id"
API_URL = "https://vidrama.asia/api/melolo"
BACKEND_URL = "https://api.shortlovers.id/api"

# Temp dir for ffmpeg processing
TEMP_DIR = Path(tempfile.gettempdir()) / "vidrama_scrape"
TEMP_DIR.mkdir(exist_ok=True)

# Timeouts and delays
API_TIMEOUT = 30
DOWNLOAD_TIMEOUT = 120
DELAY_BETWEEN_API = 0.5
DELAY_BETWEEN_EPISODES = 0.5

# S3 client singleton
_s3 = None
def get_s3():
    global _s3
    if _s3 is None:
        import boto3
        _s3 = boto3.client("s3",
            endpoint_url=R2_ENDPOINT,
            aws_access_key_id=R2_ACCESS_KEY,
            aws_secret_access_key=R2_SECRET_KEY,
        )
    return _s3


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return re.sub(r'-+', '-', text).strip('-')


# ─── DISCOVERY ───────────────────────────────────────────────

def search_all_dramas():
    """Discover all dramas from vidrama.asia Melolo search API."""
    log("\n=== DISCOVERING MELOLO DRAMAS ===\n")
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
                time.sleep(DELAY_BETWEEN_API)
            except requests.exceptions.Timeout:
                log(f"  ⏳ Timeout on '{kw}' offset={offset}, skipping")
                break
            except Exception as e:
                log(f"  ⚠️ Error '{kw}': {str(e)[:50]}")
                break
        log(f"  '{kw}' → {len(all_dramas)} unique", flush=True)
        time.sleep(DELAY_BETWEEN_API)

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

    log(f"\n  Total: {len(all_dramas)} unique dramas\n")
    return list(all_dramas.values())


def get_existing_titles():
    """Get existing drama titles from backend."""
    try:
        r = requests.get(f"{BACKEND_URL}/dramas?limit=500", timeout=5)
        if r.status_code == 200:
            data = r.json()
            items = data if isinstance(data, list) else data.get("dramas", [])
            return {d["title"] for d in items}
    except:
        pass
    return set()


# ─── FFMPEG TRANSCODING ──────────────────────────────────────

def transcode_video(input_path: Path, output_path: Path) -> bool:
    """Transcode video using user's ffmpeg command.
    H.264 CRF28, AAC 128k, faststart for web playback.
    """
    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-c:v", "libx264", "-preset", "fast", "-crf", "28",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-ac", "2",
        "-movflags", "+faststart",
        str(output_path)
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300
        )
        if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 1000:
            return True
        if result.stderr:
            log(f"        ffmpeg error: {result.stderr[-200:]}")
        return False
    except subprocess.TimeoutExpired:
        log(f"        ffmpeg timeout (>300s)")
        return False
    except Exception as e:
        log(f"        ffmpeg exception: {e}")
        return False


# ─── DOWNLOAD + UPLOAD ───────────────────────────────────────

def download_mp4(proxy_url: str, output_path: Path) -> bool:
    """Download MP4 from vidrama proxy URL."""
    full_url = f"https://vidrama.asia{proxy_url}" if proxy_url.startswith("/") else proxy_url
    try:
        resp = requests.get(full_url, timeout=DOWNLOAD_TIMEOUT, stream=True)
        resp.raise_for_status()
        total = 0
        with open(output_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
                total += len(chunk)
        if total > 1000:
            return True
        return False
    except Exception as e:
        log(f"        Download error: {str(e)[:60]}")
        return False


def upload_to_r2(file_path: Path, r2_key: str) -> bool:
    """Upload file to R2."""
    try:
        ct = "video/mp4" if r2_key.endswith(".mp4") else "image/webp"
        s3 = get_s3()
        s3.upload_file(str(file_path), R2_BUCKET, r2_key,
            ExtraArgs={"ContentType": ct}
        )
        return True
    except Exception as e:
        log(f"        R2 upload error: {str(e)[:60]}")
        return False


def upload_cover_to_r2(url: str, r2_key: str) -> bool:
    """Download cover image and upload to R2."""
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        if len(resp.content) < 100:
            return False
        s3 = get_s3()
        s3.put_object(Bucket=R2_BUCKET, Key=r2_key,
            Body=resp.content,
            ContentType=resp.headers.get("content-type", "image/webp")
        )
        return True
    except:
        return False


# ─── BACKEND REGISTRATION ────────────────────────────────────

def register_drama(drama_info, slug, uploaded_eps):
    """Register drama + episodes in backend API."""
    try:
        payload = {
            "title": drama_info["title"],
            "description": drama_info.get("description", ""),
            "cover": f"{R2_PUBLIC}/dramas/melolo/{slug}/cover.webp",
            "provider": "melolo",
            "totalEpisodes": len(uploaded_eps),
            "isActive": True,
        }
        r = requests.post(f"{BACKEND_URL}/dramas", json=payload, timeout=10)
        if r.status_code not in [200, 201]:
            log(f"    ⚠️ Drama API error: {r.status_code} {r.text[:80]}")
            return False
        drama_id = r.json().get("id")
        for ep in uploaded_eps:
            requests.post(f"{BACKEND_URL}/episodes", json={
                "dramaId": drama_id,
                "episodeNumber": ep["number"],
                "videoUrl": ep["videoUrl"],
                "duration": ep.get("duration", 0),
            }, timeout=10)
        return True
    except Exception as e:
        log(f"    ⚠️ Backend error: {e}")
        return False


# ─── MAIN ────────────────────────────────────────────────────

def process_drama(drama, slug):
    """Process a single drama: detail → download → transcode → R2."""
    drama_id = drama["id"]
    title = drama["title"]

    # Get episode list
    try:
        r = requests.get(f"{API_URL}?action=detail&id={drama_id}", timeout=API_TIMEOUT)
        if r.status_code != 200:
            log(f"  ❌ Detail API failed: {r.status_code}")
            return None
        detail = r.json().get("data", {})
    except Exception as e:
        log(f"  ❌ Detail error: {e}")
        return None

    episodes = detail.get("episodes", [])
    if not episodes:
        log(f"  ❌ No episodes")
        return None

    total_eps = len(episodes)
    log(f"  Episodes: {total_eps}")

    # Upload cover
    cover_url = drama.get("image") or drama.get("poster", "")
    if cover_url:
        ok = upload_cover_to_r2(cover_url, f"dramas/melolo/{slug}/cover.webp")
        log(f"  Cover: {'✅' if ok else '❌'}")

    # Process each episode
    uploaded = []
    drama_temp = TEMP_DIR / slug
    drama_temp.mkdir(exist_ok=True)

    for ep in episodes:
        ep_num = ep.get("episodeNumber", 0)
        if ep_num == 0:
            continue

        r2_key = f"dramas/melolo/{slug}/ep{ep_num:03d}.mp4"
        log(f"    Ep {ep_num:3}/{total_eps}:", end="", flush=True)

        # Get stream URL
        try:
            sr = requests.get(
                f"{API_URL}?action=stream&id={drama_id}&episode={ep_num}",
                timeout=API_TIMEOUT
            )
            if sr.status_code != 200:
                log(f" ❌ Stream API {sr.status_code}")
                time.sleep(DELAY_BETWEEN_EPISODES)
                continue
            stream_data = sr.json().get("data", {})
        except Exception as e:
            log(f" ❌ Stream error: {str(e)[:40]}")
            time.sleep(DELAY_BETWEEN_EPISODES)
            continue

        proxy_url = stream_data.get("proxyUrl", "")
        if not proxy_url:
            log(f" ❌ No proxy URL")
            time.sleep(DELAY_BETWEEN_EPISODES)
            continue

        # Download raw MP4
        raw_path = drama_temp / f"raw_ep{ep_num:03d}.mp4"
        transcoded_path = drama_temp / f"ep{ep_num:03d}.mp4"

        log(f" DL", end="", flush=True)
        if not download_mp4(proxy_url, raw_path):
            log(f" ❌ Download fail")
            time.sleep(DELAY_BETWEEN_EPISODES)
            continue

        raw_size = raw_path.stat().st_size / 1024 / 1024
        log(f"({raw_size:.1f}MB)", end="", flush=True)

        # Transcode with ffmpeg
        log(f" → FFmpeg", end="", flush=True)
        if not transcode_video(raw_path, transcoded_path):
            log(f" ❌ Transcode fail")
            # Fallback: upload raw if transcode fails
            log(f" (uploading raw)", end="", flush=True)
            transcoded_path = raw_path

        out_size = transcoded_path.stat().st_size / 1024 / 1024
        ratio = (1 - out_size / raw_size) * 100 if raw_size > 0 else 0
        log(f"({out_size:.1f}MB, {ratio:+.0f}%)", end="", flush=True)

        # Upload to R2
        log(f" → R2", end="", flush=True)
        if upload_to_r2(transcoded_path, r2_key):
            log(f" ✅")
            uploaded.append({
                "number": ep_num,
                "videoUrl": f"{R2_PUBLIC}/{r2_key}",
                "duration": ep.get("duration", 0),
            })
        else:
            log(f" ❌ Upload fail")

        # Cleanup temp files
        raw_path.unlink(missing_ok=True)
        transcoded_path.unlink(missing_ok=True)

        time.sleep(DELAY_BETWEEN_EPISODES)

    # Cleanup drama temp dir
    shutil.rmtree(drama_temp, ignore_errors=True)

    return uploaded


def main():
    do_scrape = "--scrape" in sys.argv
    limit = None
    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        if idx + 1 < len(sys.argv):
            limit = int(sys.argv[idx + 1])

    log("=" * 70)
    log("  VIDRAMA → R2 MP4 SCRAPER (with FFmpeg)")
    log(f"  Mode: {'FULL SCRAPE' if do_scrape else 'DISCOVERY ONLY'}")
    if limit:
        log(f"  Limit: {limit} dramas")
    log("=" * 70)

    # Discover
    dramas = search_all_dramas()

    # Save
    with open("vidrama_all_dramas.json", "w", encoding="utf-8") as f:
        json.dump(dramas, f, indent=2, ensure_ascii=False)

    # Print list
    for i, d in enumerate(sorted(dramas, key=lambda x: x["title"]), 1):
        log(f"  {i:3}. {d['title']}")

    if not do_scrape:
        log(f"\n  Run with --scrape to start downloading")
        return

    # Filter new dramas
    existing = get_existing_titles()
    new_dramas = [d for d in dramas if d["title"] not in existing]
    log(f"\n  DB has: {len(existing)} dramas")
    log(f"  New to scrape: {len(new_dramas)}")

    if limit:
        new_dramas = new_dramas[:limit]

    if not new_dramas:
        log("  Nothing new!")
        return

    # Scrape
    stats = {"ok": 0, "fail": 0, "eps": 0}
    for i, drama in enumerate(new_dramas, 1):
        slug = slugify(drama["title"])
        log(f"\n{'─' * 60}")
        log(f"  [{i}/{len(new_dramas)}] {drama['title']}")
        log(f"  Slug: {slug}")

        uploaded = process_drama(drama, slug)

        if uploaded:
            drama["description"] = drama.get("description", "")
            if register_drama(drama, slug, uploaded):
                stats["ok"] += 1
                stats["eps"] += len(uploaded)
            else:
                stats["fail"] += 1
        else:
            stats["fail"] += 1

        time.sleep(1)

    log(f"\n{'=' * 70}")
    log(f"  DONE: {stats['ok']} dramas, {stats['eps']} episodes")
    log(f"  Failed: {stats['fail']}")
    log(f"{'=' * 70}")


if __name__ == "__main__":
    main()

