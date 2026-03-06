#!/usr/bin/env python3
"""
FAST VIDRAMA SCRAPER — Skips discovery, uses cached drama list.
Uses vidrama_all_dramas.json from previous discovery.
"""
import requests, json, time, os, sys, subprocess, tempfile, shutil
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
BACKEND_URL = "https://api.shortlovers.id/api"
TEMP_DIR = Path(tempfile.gettempdir()) / "vidrama_scrape"
TEMP_DIR.mkdir(exist_ok=True)

LOG_FILE = Path(__file__).parent / "vidrama_scrape.log"

# S3 client
_s3 = None
def get_s3():
    global _s3
    if not _s3:
        import boto3
        _s3 = boto3.client("s3", endpoint_url=R2_ENDPOINT,
            aws_access_key_id=R2_ACCESS_KEY, aws_secret_access_key=R2_SECRET_KEY,
            region_name="auto")
    return _s3

def slugify(text):
    import re
    s = text.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    return re.sub(r'[-\s]+', '-', s).strip('-')

def log(msg="", end="\n"):
    print(msg, end=end, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + end)

def get_existing_titles():
    try:
        r = requests.get(f"{BACKEND_URL}/dramas?limit=500&includeInactive=true", timeout=15)
        if r.status_code == 200:
            data = r.json()
            items = data if isinstance(data, list) else data.get("dramas", [])
            return {d["title"] for d in items}
    except Exception as e:
        log(f"  Warning: Could not get existing titles: {e}")
    return set()

def check_r2_exists(slug):
    """Check if drama already has files in R2 (old or new path)."""
    try:
        for prefix in [f"dramas/melolo/{slug}/", f"melolo/{slug}/"]:
            resp = get_s3().list_objects_v2(Bucket=R2_BUCKET, Prefix=prefix, MaxKeys=2)
            if resp.get("KeyCount", 0) > 0:
                return True
        return False
    except:
        return False

def download_mp4(proxy_url, output_path):
    try:
        r = requests.get(proxy_url, stream=True, timeout=180)
        if r.status_code != 200:
            return False
        with open(output_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024*1024):
                f.write(chunk)
        return output_path.stat().st_size > 100_000
    except:
        return False

def upload_to_r2(file_path, r2_key):
    try:
        get_s3().upload_file(str(file_path), R2_BUCKET, r2_key,
            ExtraArgs={"ContentType": "video/mp4"})
        return True
    except Exception as e:
        log(f" R2 error: {e}")
        return False

def upload_cover_to_r2(url, r2_key):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = requests.get(url, timeout=20, headers=headers)
        if r.status_code != 200:
            log(f"    Cover DL status: {r.status_code}")
            return False
        if len(r.content) < 1000:
            log(f"    Cover too small: {len(r.content)} bytes")
            return False
        tmp = TEMP_DIR / "cover_tmp.webp"
        tmp.write_bytes(r.content)
        ct_map = {".webp": "image/webp", ".jpg": "image/jpeg", ".png": "image/png"}
        ext = r2_key.rsplit('.', 1)[-1] if '.' in r2_key else 'webp'
        ct = ct_map.get(f".{ext}", "image/webp")
        get_s3().upload_file(str(tmp), R2_BUCKET, r2_key,
            ExtraArgs={"ContentType": ct})
        tmp.unlink(missing_ok=True)
        return True
    except Exception as e:
        log(f"    Cover upload error: {e}")
        return False

def register_drama(drama_info, slug, uploaded_eps):
    try:
        payload = {
            "title": drama_info["title"],
            "description": drama_info.get("description", ""),
            "cover": f"{R2_PUBLIC}/dramas/melolo/{slug}/cover.webp",
            "provider": "melolo",
            "totalEpisodes": len(uploaded_eps),
            "isActive": True,
        }
        r = requests.post(f"{BACKEND_URL}/dramas", json=payload, timeout=15)
        if r.status_code not in [200, 201]:
            log(f"    Drama API error: {r.status_code} {r.text[:80]}")
            return False
        drama_id = r.json().get("id")
        for ep in uploaded_eps:
            requests.post(f"{BACKEND_URL}/episodes", json={
                "dramaId": drama_id,
                "episodeNumber": ep["number"],
                "videoUrl": ep["videoUrl"],
                "duration": ep.get("duration", 0),
            }, timeout=15)
        return True
    except Exception as e:
        log(f"    Backend error: {e}")
        return False

def process_drama(drama, slug):
    drama_id = drama["id"]
    try:
        r = requests.get(f"{API_URL}?action=detail&id={drama_id}", timeout=30)
        if r.status_code != 200:
            log(f"  Detail API failed: {r.status_code}")
            return None
        detail = r.json().get("data", {})
    except Exception as e:
        log(f"  Detail error: {e}")
        return None

    # Extract description from detail API (richer than cached)
    description = (
        detail.get("description") or detail.get("synopsis") or
        drama.get("description") or drama.get("synopsis") or ""
    )
    drama["description"] = description
    if description:
        log(f"  Desc: {description[:80]}...")

    episodes = detail.get("episodes", [])
    if not episodes:
        log(f"  No episodes")
        return None

    total_eps = len(episodes)
    log(f"  Episodes: {total_eps}")

    # Upload cover — try multiple sources
    cover_urls = [
        detail.get("image"), detail.get("poster"), detail.get("cover"),
        drama.get("image"), drama.get("poster"), drama.get("originalImage"),
    ]
    cover_ok = False
    for cover_url in cover_urls:
        if cover_url:
            cover_ok = upload_cover_to_r2(cover_url, f"dramas/melolo/{slug}/cover.webp")
            if cover_ok:
                break
    log(f"  Cover: {'OK' if cover_ok else 'FAIL'}")

    # Process each episode
    uploaded = []
    drama_temp = TEMP_DIR / slug
    drama_temp.mkdir(exist_ok=True)

    for ep in episodes:
        ep_num = ep.get("episodeNumber", 0)
        if ep_num == 0:
            continue

        r2_key = f"dramas/melolo/{slug}/ep{ep_num:03d}.mp4"
        log(f"    Ep {ep_num:3}/{total_eps}:", end="")

        # Get stream URL with retry
        proxy_url = None
        for attempt in range(3):
            try:
                sr = requests.get(
                    f"{API_URL}?action=stream&id={drama_id}&episode={ep_num}",
                    timeout=30
                )
                if sr.status_code == 200:
                    raw_url = sr.json().get("data", {}).get("proxyUrl", "")
                    if raw_url:
                        # proxyUrl is relative like /api/video-proxy?videoId=...
                        if raw_url.startswith("/"):
                            proxy_url = f"https://vidrama.asia{raw_url}"
                        elif raw_url.startswith("http"):
                            proxy_url = raw_url
                        else:
                            proxy_url = f"https://vidrama.asia/{raw_url}"
                        break
            except:
                pass
            time.sleep(1)

        if not proxy_url:
            log(f" NO URL")
            continue

        # Download
        raw_path = drama_temp / f"ep{ep_num:03d}.mp4"
        log(f" DL", end="")
        if not download_mp4(proxy_url, raw_path):
            log(f" FAIL")
            raw_path.unlink(missing_ok=True)
            continue

        size_mb = raw_path.stat().st_size / 1024 / 1024
        log(f"({size_mb:.1f}MB)", end="")

        # Upload to R2 directly (skip FFmpeg for speed)
        log(f" R2", end="")
        if upload_to_r2(raw_path, r2_key):
            log(f" OK")
            uploaded.append({
                "number": ep_num,
                "videoUrl": f"{R2_PUBLIC}/{r2_key}",
                "duration": ep.get("duration", 0),
            })
        else:
            log(f" FAIL")

        raw_path.unlink(missing_ok=True)
        time.sleep(0.3)

    shutil.rmtree(drama_temp, ignore_errors=True)
    return uploaded


def main():
    # Clear log
    open(LOG_FILE, "w").close()

    limit = None
    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        if idx + 1 < len(sys.argv):
            limit = int(sys.argv[idx + 1])

    log("=" * 60)
    log("  VIDRAMA FAST SCRAPER (skip discovery)")
    log("=" * 60)

    # Load cached drama list
    cache_file = Path(__file__).parent / "vidrama_all_dramas.json"
    if not cache_file.exists():
        log("ERROR: vidrama_all_dramas.json not found!")
        log("Run: python vidrama_to_r2.py  (without --scrape) first")
        return

    dramas = json.loads(cache_file.read_text(encoding="utf-8"))
    log(f"  Cached dramas: {len(dramas)}")

    # Filter out existing
    existing = get_existing_titles()
    new_dramas = [d for d in dramas if d["title"] not in existing]
    log(f"  Already in DB: {len(existing)}")
    log(f"  New to scrape: {len(new_dramas)}")

    if limit:
        new_dramas = new_dramas[:limit]
        log(f"  Limited to: {limit}")

    if not new_dramas:
        log("  Nothing new to scrape!")
        return

    # Scrape
    stats = {"ok": 0, "fail": 0, "eps": 0}
    for i, drama in enumerate(new_dramas, 1):
        slug = slugify(drama["title"])
        log(f"\n{'_' * 60}")
        log(f"  [{i}/{len(new_dramas)}] {drama['title']}")
        log(f"  Slug: {slug}")

        # Skip if already uploaded to R2
        if check_r2_exists(slug):
            log(f"  SKIP: Already in R2")
            stats["ok"] += 1
            continue

        uploaded = process_drama(drama, slug)
        if uploaded:
            if register_drama(drama, slug, uploaded):
                stats["ok"] += 1
                stats["eps"] += len(uploaded)
                log(f"  REGISTERED: {len(uploaded)} episodes")
            else:
                stats["fail"] += 1
        else:
            stats["fail"] += 1

        time.sleep(1)

    log(f"\n{'=' * 60}")
    log(f"  DONE: {stats['ok']} dramas, {stats['eps']} episodes")
    log(f"  Failed: {stats['fail']}")
    log(f"{'=' * 60}")


if __name__ == "__main__":
    main()
