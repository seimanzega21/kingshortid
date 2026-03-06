#!/usr/bin/env python3
"""
DOWNLOAD MISSING EPISODES
==========================
Reads audit results, downloads missing episodes from Vidrama API,
uploads to R2, and registers in DB via Prisma-compatible JSON output.

Processes dramas where API has more episodes than R2/DB.

Usage:
  python download_missing_eps.py              # Process all incomplete dramas
  python download_missing_eps.py --workers 2  # Use 2 parallel workers
"""
import requests, json, time, os, re, sys, tempfile
from pathlib import Path
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

load_dotenv()

R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET = os.getenv("R2_BUCKET_NAME")
R2_PUBLIC = "https://stream.shortlovers.id"
API_URL = "https://vidrama.asia/api/melolo"

TEMP_DIR = Path(tempfile.gettempdir()) / "vidrama_missing"
TEMP_DIR.mkdir(exist_ok=True)

DOWNLOAD_TIMEOUT = 120
API_TIMEOUT = 15

_local = threading.local()
_print_lock = threading.Lock()
stats_lock = threading.Lock()
stats = {"downloaded": 0, "failed": 0, "skipped": 0}

def tprint(msg):
    with _print_lock:
        print(msg, flush=True)

def get_s3():
    if not hasattr(_local, 's3'):
        import boto3
        _local.s3 = boto3.client("s3",
            endpoint_url=R2_ENDPOINT,
            aws_access_key_id=R2_ACCESS_KEY,
            aws_secret_access_key=R2_SECRET_KEY)
    return _local.s3

def r2_key_exists(key):
    try:
        get_s3().head_object(Bucket=R2_BUCKET, Key=key)
        return True
    except:
        return False

def download_mp4(proxy_url, output_path, tag=""):
    full_url = f"https://vidrama.asia{proxy_url}" if proxy_url.startswith("/") else proxy_url
    try:
        resp = requests.get(full_url, timeout=DOWNLOAD_TIMEOUT, stream=True)
        resp.raise_for_status()
        total = 0
        with open(output_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=1024*1024):
                f.write(chunk)
                total += len(chunk)
        return total > 1000
    except:
        return False

def upload_to_r2(file_path, r2_key):
    try:
        get_s3().upload_file(str(file_path), R2_BUCKET, r2_key,
            ExtraArgs={"ContentType": "video/mp4"})
        return True
    except Exception as e:
        tprint(f"        R2 error: {str(e)[:60]}")
        return False

def process_drama(issue, idx, total):
    slug = issue["slug"]
    title = issue["title"]
    vidrama_id = issue.get("vidramaId", "")
    db_eps = issue["dbEps"]
    r2_eps = issue["r2Eps"]
    api_eps = issue["apiEps"]
    tag = f"[{idx}/{total}]"

    tprint(f"\n{'─' * 60}")
    tprint(f"  {tag} {title}")
    tprint(f"  DB: {db_eps} | R2: {r2_eps} | API: {api_eps} | Missing: {api_eps - max(db_eps, r2_eps)}")

    if not vidrama_id:
        tprint(f"  {tag} ❌ No Vidrama ID — skipping")
        with stats_lock:
            stats["skipped"] += 1
        return

    # Get episode list from API
    try:
        r = requests.get(f"{API_URL}?action=detail&id={vidrama_id}", timeout=API_TIMEOUT)
        if r.status_code != 200:
            tprint(f"  {tag} ❌ Detail API failed")
            with stats_lock:
                stats["failed"] += 1
            return
        detail = r.json().get("data", {})
    except Exception as e:
        tprint(f"  {tag} ❌ API error: {e}")
        with stats_lock:
            stats["failed"] += 1
        return

    episodes = detail.get("episodes", [])
    if not episodes:
        tprint(f"  {tag} ❌ No episodes in API")
        with stats_lock:
            stats["failed"] += 1
        return

    # Find episodes missing from R2
    drama_temp = TEMP_DIR / slug
    drama_temp.mkdir(exist_ok=True)
    downloaded = 0
    failed_eps = 0

    for ep in episodes:
        ep_num = ep.get("episodeNumber", 0)
        if ep_num == 0:
            continue

        r2_key = f"melolo/{slug}/ep{ep_num:03d}.mp4"

        # Skip if already exists in R2
        if r2_key_exists(r2_key):
            continue

        # Download
        raw_path = drama_temp / f"ep{ep_num:03d}.mp4"
        success = False

        for attempt in range(3):
            try:
                sr = requests.get(
                    f"{API_URL}?action=stream&id={vidrama_id}&episode={ep_num}",
                    timeout=API_TIMEOUT)
                if sr.status_code != 200:
                    time.sleep(2 * (attempt + 1))
                    continue
                stream_data = sr.json().get("data", {})
            except:
                time.sleep(2 * (attempt + 1))
                continue

            proxy_url = stream_data.get("proxyUrl", "")
            if not proxy_url:
                time.sleep(2 * (attempt + 1))
                continue

            if download_mp4(proxy_url, raw_path, tag):
                success = True
                break

            raw_path.unlink(missing_ok=True)
            time.sleep(2 * (attempt + 1))

        if not success:
            tprint(f"    {tag} Ep {ep_num:3}: ❌ Failed after 3 attempts")
            raw_path.unlink(missing_ok=True)
            failed_eps += 1
            continue

        file_mb = raw_path.stat().st_size / 1024 / 1024

        if upload_to_r2(raw_path, r2_key):
            tprint(f"    {tag} Ep {ep_num:3}: ✅ {file_mb:.1f}MB")
            downloaded += 1
        else:
            tprint(f"    {tag} Ep {ep_num:3}: ❌ Upload failed")
            failed_eps += 1

        # Cleanup
        for _ in range(3):
            try:
                raw_path.unlink(missing_ok=True)
                break
            except OSError:
                time.sleep(0.5)
        time.sleep(0.3)

    # Cleanup temp dir
    try:
        drama_temp.rmdir()
    except:
        pass

    tprint(f"  {tag} Done: +{downloaded} eps downloaded, {failed_eps} failed")

    with stats_lock:
        stats["downloaded"] += downloaded
        stats["failed"] += failed_eps


def main():
    workers = 2  # Conservative: 2 workers for missing eps

    if "--workers" in sys.argv:
        idx = sys.argv.index("--workers")
        if idx + 1 < len(sys.argv):
            workers = int(sys.argv[idx + 1])

    # Load audit results
    script_dir = os.path.dirname(os.path.abspath(__file__))
    audit_path = os.path.join(script_dir, "..", "admin", "episode_audit_result.json")
    if not os.path.exists(audit_path):
        # Try current dir
        audit_path = os.path.join(script_dir, "episode_audit_result.json")
    if not os.path.exists(audit_path):
        print("❌ episode_audit_result.json not found! Run audit_episodes.js first.")
        return

    with open(audit_path, "r", encoding="utf-8") as f:
        audit = json.load(f)

    issues = audit.get("issues", [])

    # Filter: only dramas where API has more episodes than R2
    to_process = [i for i in issues if i["apiEps"] > max(i["r2Eps"], i["dbEps"]) and i.get("vidramaId")]

    print("=" * 60)
    print("  DOWNLOAD MISSING EPISODES")
    print(f"  Workers: {workers}")
    print("=" * 60)
    print(f"\n  Total issues: {len(issues)}")
    print(f"  Need download: {len(to_process)}")

    total_missing = sum(i["apiEps"] - max(i["r2Eps"], i["dbEps"]) for i in to_process)
    print(f"  Total missing episodes: ~{total_missing}")

    if not to_process:
        print("  Nothing to download!")
        return

    # Sort by most missing first
    to_process.sort(key=lambda x: x["apiEps"] - max(x["r2Eps"], x["dbEps"]), reverse=True)

    print(f"\n  Top 10 most incomplete:")
    for i, issue in enumerate(to_process[:10], 1):
        missing = issue["apiEps"] - max(issue["r2Eps"], issue["dbEps"])
        print(f"    {i:2}. {issue['title'][:40]:<40} missing {missing}")

    print(f"\n  Starting {workers} workers...\n")

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {}
        for i, issue in enumerate(to_process, 1):
            f = executor.submit(process_drama, issue, i, len(to_process))
            futures[f] = issue["title"]

        for f in as_completed(futures):
            try:
                f.result()
            except Exception as e:
                tprint(f"  ❌ Exception: {e}")

    print(f"\n{'=' * 60}")
    print(f"  DONE!")
    print(f"  Downloaded: {stats['downloaded']} episodes")
    print(f"  Failed: {stats['failed']}")
    print(f"  Skipped: {stats['skipped']}")
    print(f"{'=' * 60}")
    print(f"\n  Now run to register new episodes in DB:")
    print(f"    cd admin && node audit_episodes.js --fix")

if __name__ == "__main__":
    main()
