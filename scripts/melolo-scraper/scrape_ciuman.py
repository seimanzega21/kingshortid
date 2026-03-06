#!/usr/bin/env python3
"""
Targeted Scraper: Ciuman Pengakuan Manis - Episodes 8-96
=========================================================
Downloads missing episodes from Vidrama, uploads raw MP4 to R2,
and registers them in the Cloudflare Worker backend.

Usage:
  python scrape_ciuman.py                    # Dry run - show what would be scraped
  python scrape_ciuman.py --scrape           # Full scrape + upload + register
  python scrape_ciuman.py --scrape --start 8 # Start from specific episode
"""
import requests, json, time, os, sys, tempfile, shutil
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ─── CONFIG ──────────────────────────────────────────────────
VIDRAMA_ID = "7562087033263361029"
DRAMA_TITLE = "Ciuman Pengakuan Manis"
SLUG = "ciuman-pengakuan-manis"
VIDRAMA_API = "https://vidrama.asia/api/melolo"
WORKER_API = "https://api.shortlovers.id/api"
R2_PUBLIC = "https://stream.shortlovers.id"

# R2 config from env
R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET = os.getenv("R2_BUCKET_NAME")

# Temp dir
TEMP_DIR = Path(tempfile.gettempdir()) / "vidrama_ciuman"
TEMP_DIR.mkdir(exist_ok=True)

# Timeouts
API_TIMEOUT = 15
DOWNLOAD_TIMEOUT = 180
DELAY_BETWEEN_EPISODES = 1

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


# ─── STEP 1: Find Drama ID in Backend ───────────────────────
def find_drama_id():
    """Find the drama ID from the Worker backend."""
    print("\n🔍 Looking for drama in backend...")
    try:
        r = requests.get(f"{WORKER_API}/dramas?limit=500", timeout=10)
        if r.status_code == 200:
            resp = r.json()
            dramas = resp if isinstance(resp, list) else resp.get("dramas", [])
            for d in dramas:
                if "Ciuman Pengakuan" in d.get("title", ""):
                    print(f"  ✅ Found: {d['title']} (ID: {d['id']})")
                    print(f"  Current episodes: {d.get('totalEpisodes', '?')}")
                    return d["id"]
            print("  ❌ Drama not found in backend!")
            return None
        else:
            print(f"  ❌ API error: {r.status_code}")
            return None
    except Exception as e:
        print(f"  ❌ Connection error: {e}")
        return None


# ─── STEP 2: Get Existing Episodes ──────────────────────────
def get_existing_episodes(drama_id):
    """Get list of episodes already in the backend."""
    try:
        r = requests.get(f"{WORKER_API}/dramas/{drama_id}/episodes", timeout=10)
        if r.status_code == 200:
            data = r.json()
            eps = data if isinstance(data, list) else data.get("episodes", [])
            return {e.get("episodeNumber", 0) for e in eps}
    except Exception as e:
        print(f"  ⚠️ Could not fetch existing episodes: {e}")
    return set()


# ─── STEP 3: Get Vidrama Episode List ───────────────────────
def get_vidrama_episodes():
    """Get full episode list from Vidrama API."""
    print("\n📺 Fetching episodes from Vidrama...")
    try:
        r = requests.get(
            f"{VIDRAMA_API}?action=detail&id={VIDRAMA_ID}",
            timeout=API_TIMEOUT
        )
        if r.status_code != 200:
            print(f"  ❌ Vidrama API error: {r.status_code}")
            return []
        episodes = r.json().get("data", {}).get("episodes", [])
        print(f"  ✅ Found {len(episodes)} episodes on Vidrama")
        return episodes
    except Exception as e:
        print(f"  ❌ Vidrama error: {e}")
        return []


# ─── STEP 4: Download from Vidrama ──────────────────────────
def download_episode(ep_num):
    """Download a single episode from Vidrama proxy."""
    # Get stream URL with retry
    for attempt in range(3):
        try:
            sr = requests.get(
                f"{VIDRAMA_API}?action=stream&id={VIDRAMA_ID}&episode={ep_num}",
                timeout=API_TIMEOUT
            )
            if sr.status_code != 200:
                if attempt < 2:
                    time.sleep(2)
                    continue
                return None
            stream_data = sr.json().get("data", {})
            proxy_url = stream_data.get("proxyUrl", "")
            if not proxy_url:
                if attempt < 2:
                    time.sleep(2)
                    continue
                return None
            break
        except Exception as e:
            if attempt < 2:
                time.sleep(2)
                continue
            print(f" ❌ Stream error: {str(e)[:40]}")
            return None

    # Download MP4
    full_url = f"https://vidrama.asia{proxy_url}" if proxy_url.startswith("/") else proxy_url
    output_path = TEMP_DIR / f"ep{ep_num:03d}.mp4"

    try:
        resp = requests.get(full_url, timeout=DOWNLOAD_TIMEOUT, stream=True)
        resp.raise_for_status()
        total = 0
        with open(output_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
                total += len(chunk)
        if total > 1000:
            return output_path
        output_path.unlink(missing_ok=True)
        return None
    except Exception as e:
        print(f" ❌ DL error: {str(e)[:50]}")
        output_path.unlink(missing_ok=True)
        return None


# ─── STEP 5: Upload to R2 ───────────────────────────────────
def upload_to_r2(file_path, r2_key):
    """Upload MP4 file to R2."""
    try:
        s3 = get_s3()
        s3.upload_file(str(file_path), R2_BUCKET, r2_key,
            ExtraArgs={"ContentType": "video/mp4"}
        )
        return True
    except Exception as e:
        print(f" ❌ R2 error: {str(e)[:50]}")
        return False


# ─── STEP 6: Register in Backend ────────────────────────────
def register_episode(drama_id, ep_num, video_url, duration):
    """Register episode in Worker backend."""
    try:
        payload = {
            "dramaId": drama_id,
            "episodeNumber": ep_num,
            "videoUrl": video_url,
            "duration": duration,
        }
        r = requests.post(f"{WORKER_API}/episodes", json=payload, timeout=15)
        if r.status_code in [200, 201]:
            return True
        else:
            print(f" ❌ Register error: {r.status_code} {r.text[:80]}")
            return False
    except Exception as e:
        print(f" ❌ Register error: {e}")
        return False


# ─── MAIN ────────────────────────────────────────────────────
def main():
    do_scrape = "--scrape" in sys.argv
    start_ep = 8
    if "--start" in sys.argv:
        idx = sys.argv.index("--start")
        if idx + 1 < len(sys.argv):
            start_ep = int(sys.argv[idx + 1])

    print("=" * 60)
    print(f"  SCRAPER: {DRAMA_TITLE}")
    print(f"  Mode: {'FULL SCRAPE' if do_scrape else 'DRY RUN'}")
    print(f"  Start from: Episode {start_ep}")
    print("=" * 60)

    # Step 1: Find drama in backend
    drama_id = find_drama_id()
    if not drama_id:
        print("\n⛔ Cannot proceed without backend drama ID!")
        print("   Make sure the Worker API is accessible.")
        return

    # Step 2: Get existing episodes
    existing = get_existing_episodes(drama_id)
    print(f"\n  Existing episodes in DB: {sorted(existing) if existing else 'none found'}")

    # Step 3: Get Vidrama episode list
    vidrama_eps = get_vidrama_episodes()
    if not vidrama_eps:
        print("\n⛔ No episodes from Vidrama!")
        return

    # Filter to missing episodes
    missing = [
        ep for ep in vidrama_eps
        if ep.get("episodeNumber", 0) >= start_ep
        and ep.get("episodeNumber", 0) not in existing
    ]
    missing.sort(key=lambda x: x.get("episodeNumber", 0))

    print(f"\n  Missing episodes: {len(missing)}")
    if missing:
        nums = [ep.get("episodeNumber", 0) for ep in missing]
        print(f"  Episodes to scrape: {nums[0]}-{nums[-1]}")

    if not do_scrape:
        print(f"\n  Run with --scrape to start downloading")
        print(f"  Example: python scrape_ciuman.py --scrape --start {start_ep}")
        return

    # Step 4-6: Scrape loop
    stats = {"ok": 0, "fail": 0, "total": len(missing)}

    for i, ep in enumerate(missing, 1):
        ep_num = ep.get("episodeNumber", 0)
        duration = ep.get("duration", 0)
        r2_key = f"melolo/{SLUG}/ep{ep_num:03d}.mp4"
        video_url = f"{R2_PUBLIC}/{r2_key}"

        print(f"\n  [{i}/{len(missing)}] Episode {ep_num}:", end="", flush=True)

        # Download
        print(f" DL", end="", flush=True)
        mp4_path = download_episode(ep_num)
        if not mp4_path:
            print(f" ❌ Download failed")
            stats["fail"] += 1
            time.sleep(DELAY_BETWEEN_EPISODES)
            continue

        size_mb = mp4_path.stat().st_size / 1024 / 1024
        print(f"({size_mb:.1f}MB)", end="", flush=True)

        # Upload to R2
        print(f" → R2", end="", flush=True)
        if not upload_to_r2(mp4_path, r2_key):
            print(f" ❌ Upload failed")
            mp4_path.unlink(missing_ok=True)
            stats["fail"] += 1
            time.sleep(DELAY_BETWEEN_EPISODES)
            continue

        # Register in backend
        print(f" → DB", end="", flush=True)
        if register_episode(drama_id, ep_num, video_url, duration):
            print(f" ✅")
            stats["ok"] += 1
        else:
            print(f" ⚠️ R2 ok, but DB registration failed")
            stats["ok"] += 1  # R2 upload succeeded at least

        # Cleanup
        mp4_path.unlink(missing_ok=True)
        time.sleep(DELAY_BETWEEN_EPISODES)

    # Summary
    print(f"\n{'=' * 60}")
    print(f"  DONE!")
    print(f"  Uploaded: {stats['ok']}/{stats['total']} episodes")
    print(f"  Failed:   {stats['fail']}/{stats['total']} episodes")
    print(f"{'=' * 60}")

    # Cleanup temp dir
    shutil.rmtree(TEMP_DIR, ignore_errors=True)


if __name__ == "__main__":
    main()
