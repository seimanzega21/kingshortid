"""
backfill_540p.py — Encode 540P for all existing microdrama episodes in R2.

Logic:
  - List all ep*.mp4 (720P) files in R2 under dramas/microdrama/
  - Skip if ep*_540p.mp4 already exists
  - Download 720P from R2, encode to 540P with ffmpeg, upload back to R2
  - PATCH /api/episodes to register videoUrl540p in the DB
  - Uses thread pool for parallelism
"""

import os, sys, threading, subprocess, shutil, requests, tempfile
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import boto3
from botocore.config import Config

load_dotenv()  # reads .env from current directory

R2_ENDPOINT   = os.getenv("R2_ENDPOINT", "")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET     = os.getenv("R2_BUCKET_NAME", "kingshortid")
R2_PUBLIC     = "https://stream.shortlovers.id"
BACKEND_URL   = os.getenv("BACKEND_URL", "https://api.shortlovers.id/api")
ADMIN_KEY     = os.getenv("ADMIN_KEY", "")

TEMP_DIR = Path(tempfile.gettempdir()) / "backfill540p"
TEMP_DIR.mkdir(exist_ok=True)

WORKERS = 4   # lower than scraper to not overload CPU during encode

_lock = threading.Lock()

def tprint(*args, **kwargs):
    with _lock:
        print(*args, flush=True, **kwargs)

def get_s3():
    return boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )

def list_r2_keys(s3, prefix):
    """List all keys under prefix (handles pagination)."""
    keys = []
    kwargs = {"Bucket": R2_BUCKET, "Prefix": prefix}
    while True:
        resp = s3.list_objects_v2(**kwargs)
        for obj in resp.get("Contents", []):
            keys.append(obj["Key"])
        if not resp.get("IsTruncated"):
            break
        kwargs["ContinuationToken"] = resp["NextContinuationToken"]
    return keys

def r2_key_exists(s3, key):
    try:
        s3.head_object(Bucket=R2_BUCKET, Key=key)
        return True
    except:
        return False

def get_episode_id_from_db(slug, ep_num):
    """Get episode ID from backend by drama slug + episode number."""
    try:
        # First get drama by slug via search
        r = requests.get(f"{BACKEND_URL}/dramas/search", params={"q": slug, "limit": 5}, timeout=10)
        if r.status_code != 200:
            return None
        dramas = r.json().get("dramas", [])
        for d in dramas:
            # Match by slug in cover URL
            if slug in (d.get("cover") or ""):
                drama_id = d["id"]
                er = requests.get(f"{BACKEND_URL}/dramas/{drama_id}/episodes", timeout=10)
                if er.status_code == 200:
                    for ep in er.json():
                        if ep["episodeNumber"] == ep_num:
                            return ep["id"]
        return None
    except:
        return None

def process_episode(key_720p, s3, idx, total):
    """Download 720P from R2, encode 540P, upload, update DB."""
    # key_720p example: dramas/microdrama/some-slug/ep001.mp4
    parts = key_720p.split("/")
    if len(parts) < 4:
        return
    slug = parts[2]
    ep_file = parts[3]  # ep001.mp4

    # Parse episode number
    try:
        ep_num = int(ep_file.replace("ep", "").replace(".mp4", "").replace("_540p", ""))
    except:
        return

    key_540p = key_720p.replace(".mp4", "_540p.mp4")

    # Skip if already done
    if r2_key_exists(s3, key_540p):
        tprint(f"  [{idx}/{total}] {slug}/ep{ep_num:03d}: 540P exists, skip")
        return

    work_dir = TEMP_DIR / f"{slug}_ep{ep_num}_{threading.current_thread().ident}"
    work_dir.mkdir(exist_ok=True)
    path_720p = work_dir / "in_720p.mp4"
    path_540p = work_dir / "out_540p.mp4"

    try:
        # Download 720P from R2
        tprint(f"  [{idx}/{total}] {slug}/ep{ep_num:03d}: Downloading 720P...")
        s3.download_file(R2_BUCKET, key_720p, str(path_720p))

        # Encode 540P
        res = subprocess.run([
            "ffmpeg", "-y", "-i", str(path_720p),
            "-vf", "scale=540:-2",
            "-c:v", "libx264", "-preset", "fast", "-crf", "26",
            "-movflags", "+faststart",
            "-c:a", "copy",
            str(path_540p)
        ], capture_output=True, timeout=300)

        if res.returncode != 0 or not path_540p.exists():
            tprint(f"  [{idx}/{total}] {slug}/ep{ep_num:03d}: FFmpeg FAIL")
            return

        mb_540 = path_540p.stat().st_size / 1024 / 1024
        mb_720 = path_720p.stat().st_size / 1024 / 1024

        # Upload 540P to R2
        s3.upload_file(str(path_540p), R2_BUCKET, key_540p,
                       ExtraArgs={"ContentType": "video/mp4"})

        url_540p = f"{R2_PUBLIC}/{key_540p}"
        url_720p = f"{R2_PUBLIC}/{key_720p}"

        tprint(f"  [{idx}/{total}] {slug}/ep{ep_num:03d}: OK {mb_720:.1f}MB→{mb_540:.1f}MB | {url_540p}")

        # Update DB via PATCH /api/episodes (find by videoUrl match)
        headers = {"Authorization": f"Bearer {ADMIN_KEY}"} if ADMIN_KEY else {}
        try:
            # Find episode by searching for the videoUrl
            search_url = f"{BACKEND_URL}/episodes/by-url"
            r = requests.get(search_url, params={"videoUrl": url_720p}, headers=headers, timeout=10)
            if r.status_code == 200:
                ep_id = r.json().get("id")
                if ep_id:
                    requests.patch(f"{BACKEND_URL}/episodes/{ep_id}",
                                   json={"videoUrl540p": url_540p},
                                   headers=headers, timeout=10)
        except:
            pass  # DB update is best-effort; will be picked up on next scrape

    except Exception as e:
        tprint(f"  [{idx}/{total}] {slug}/ep{ep_num:03d}: ERROR {str(e)[:60]}")
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def main():
    # Load .env if exists
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

    # Refresh globals from env
    global R2_ENDPOINT, R2_ACCESS_KEY, R2_SECRET_KEY, R2_BUCKET, R2_PUBLIC, BACKEND_URL, ADMIN_KEY
    R2_ENDPOINT   = os.environ.get("R2_ENDPOINT",   R2_ENDPOINT)
    R2_ACCESS_KEY = os.environ.get("R2_ACCESS_KEY", R2_ACCESS_KEY)
    R2_SECRET_KEY = os.environ.get("R2_SECRET_KEY", R2_SECRET_KEY)
    R2_BUCKET     = os.environ.get("R2_BUCKET",     R2_BUCKET)
    R2_PUBLIC     = os.environ.get("R2_PUBLIC",     R2_PUBLIC)
    BACKEND_URL   = os.environ.get("BACKEND_URL",   BACKEND_URL)
    ADMIN_KEY     = os.environ.get("ADMIN_KEY",     ADMIN_KEY)

    print("=" * 60)
    print("  MICRODRAMA 540P BACKFILL")
    print(f"  Workers: {WORKERS}")
    print("=" * 60)

    s3 = get_s3()

    # List all 720P episode files (exclude _540p files)
    print("\n  Listing R2 objects under dramas/microdrama/ ...")
    all_keys = list_r2_keys(s3, "dramas/microdrama/")
    ep_720p_keys = [
        k for k in all_keys
        if k.endswith(".mp4") and "_540p" not in k and "/ep" in k
    ]
    print(f"  Found {len(ep_720p_keys)} episodes to check\n")

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {
            executor.submit(process_episode, key, s3, idx + 1, len(ep_720p_keys)): key
            for idx, key in enumerate(ep_720p_keys)
        }
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                tprint(f"  WORKER ERROR: {e}")

    print("\n" + "=" * 60)
    print("  BACKFILL DONE")
    print("=" * 60)

if __name__ == "__main__":
    main()
