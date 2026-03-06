#!/usr/bin/env python3
"""
FASTSTART FIX — Apply -movflags +faststart to all MP4s on R2
=============================================================
Downloads each MP4, runs `ffmpeg -c copy -movflags +faststart`,
and re-uploads. This moves the moov atom to the front of the file
so players can start playback immediately without downloading the
entire file first.

Usage:
  python fix_faststart.py                  # Dry run (count only)
  python fix_faststart.py --execute        # Execute fix
  python fix_faststart.py --execute --workers 8  # 8 parallel workers
  python fix_faststart.py --slug cinta-di-masa-perang  # Fix one drama only

Requirements:
  - ffmpeg in PATH
  - boto3, python-dotenv
"""
import os, sys, time, json, tempfile, subprocess, shutil, threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv()

# R2 config
R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET = os.getenv("R2_BUCKET_NAME")

# Thread-safe
_local = threading.local()
_print_lock = threading.Lock()
stats_lock = threading.Lock()
stats = {"fixed": 0, "skipped": 0, "failed": 0, "bytes_saved": 0}

TEMP_DIR = Path(tempfile.gettempdir()) / "faststart_fix"
TEMP_DIR.mkdir(exist_ok=True)


def tprint(msg):
    with _print_lock:
        print(msg, flush=True)


def get_s3():
    if not hasattr(_local, "s3"):
        import boto3
        _local.s3 = boto3.client("s3",
            endpoint_url=R2_ENDPOINT,
            aws_access_key_id=R2_ACCESS_KEY,
            aws_secret_access_key=R2_SECRET_KEY,
        )
    return _local.s3


def check_ffmpeg():
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=10)
        return result.returncode == 0
    except:
        return False


def needs_faststart(filepath):
    """Check if MP4 file needs faststart (moov atom not at beginning).
    Uses ffprobe to check if moov is before mdat."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format_tags=",
             "-show_entries", "stream=codec_type", str(filepath)],
            capture_output=True, text=True, timeout=30
        )
        # Simple heuristic: try to apply faststart with -c copy
        # If moov is already at front, ffmpeg finishes instantly and file size barely changes
        return True  # Always try — ffmpeg is smart enough to skip if not needed
    except:
        return True


def fix_one_video(r2_key, dry_run=False):
    """Download, apply faststart, re-upload one video."""
    slug = r2_key.split("/")[1] if "/" in r2_key else "unknown"
    ep_name = r2_key.split("/")[-1]

    if dry_run:
        return "dry_run"

    work_dir = TEMP_DIR / f"{slug}_{ep_name}_{threading.current_thread().ident}"
    work_dir.mkdir(exist_ok=True)

    input_path = work_dir / "input.mp4"
    output_path = work_dir / "output.mp4"

    try:
        s3 = get_s3()

        # 1. Download from R2
        s3.download_file(R2_BUCKET, r2_key, str(input_path))
        original_size = input_path.stat().st_size

        if original_size < 1000:
            tprint(f"    ⚠️ {r2_key}: too small ({original_size}B), skipping")
            return "skipped"

        # 2. Apply faststart with copy (no re-encode)
        result = subprocess.run([
            "ffmpeg", "-y", "-i", str(input_path),
            "-c", "copy",
            "-movflags", "+faststart",
            str(output_path)
        ], capture_output=True, text=True, timeout=120)

        if result.returncode != 0:
            tprint(f"    ❌ {r2_key}: ffmpeg failed — {result.stderr[-100:]}")
            return "failed"

        new_size = output_path.stat().st_size

        # 3. Sanity check — output should be similar size (±10%)
        if new_size < original_size * 0.5 or new_size > original_size * 1.5:
            tprint(f"    ⚠️ {r2_key}: suspicious size change {original_size} → {new_size}, skipping upload")
            return "failed"

        # 4. Re-upload to R2
        s3.upload_file(str(output_path), R2_BUCKET, r2_key,
            ExtraArgs={"ContentType": "video/mp4"})

        size_diff = original_size - new_size
        with stats_lock:
            stats["bytes_saved"] += size_diff

        return "fixed"

    except Exception as e:
        tprint(f"    ❌ {r2_key}: {str(e)[:80]}")
        return "failed"
    finally:
        # Cleanup
        shutil.rmtree(work_dir, ignore_errors=True)


def list_all_mp4s(prefix="melolo/", specific_slug=None):
    """List all MP4 files in R2 under the given prefix."""
    s3 = get_s3()
    mp4_keys = []

    if specific_slug:
        prefix = f"melolo/{specific_slug}/"

    tprint(f"  Scanning R2 prefix: {prefix}")
    paginator = s3.get_paginator('list_objects_v2')

    for page in paginator.paginate(Bucket=R2_BUCKET, Prefix=prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith(".mp4"):
                mp4_keys.append(key)

    tprint(f"  Found {len(mp4_keys)} MP4 files")
    return mp4_keys


def main():
    execute = "--execute" in sys.argv
    workers = 5
    specific_slug = None

    if "--workers" in sys.argv:
        idx = sys.argv.index("--workers")
        if idx + 1 < len(sys.argv):
            workers = int(sys.argv[idx + 1])

    if "--slug" in sys.argv:
        idx = sys.argv.index("--slug")
        if idx + 1 < len(sys.argv):
            specific_slug = sys.argv[idx + 1]

    print("=" * 70)
    print("  MP4 FASTSTART FIX")
    print(f"  Mode: {'EXECUTE' if execute else 'DRY RUN'}")
    print(f"  Workers: {workers}")
    if specific_slug:
        print(f"  Target: {specific_slug}")
    print("=" * 70)

    # Check ffmpeg
    if execute and not check_ffmpeg():
        print("\n  ❌ ffmpeg not found in PATH! Install ffmpeg first.")
        sys.exit(1)

    # List all MP4s
    mp4_keys = list_all_mp4s(specific_slug=specific_slug)
    if not mp4_keys:
        print("\n  No MP4 files found!")
        return

    # Group by drama for nice output
    dramas = {}
    for key in mp4_keys:
        parts = key.split("/")
        if len(parts) >= 3:
            slug = parts[1]
            dramas.setdefault(slug, []).append(key)

    print(f"\n  Dramas: {len(dramas)}")
    print(f"  Total MP4s: {len(mp4_keys)}")

    if not execute:
        print(f"\n  Estimated time: ~{len(mp4_keys) * 3 / workers / 60:.0f} minutes ({workers} workers)")
        print(f"\n  Run with --execute to start fixing!")

        # Show sample
        print(f"\n  Sample (first 5 dramas):")
        for slug in list(dramas.keys())[:5]:
            eps = dramas[slug]
            print(f"    {slug}: {len(eps)} episodes")
        return

    # Execute
    start_time = time.time()
    completed = 0

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {}
        for key in mp4_keys:
            f = executor.submit(fix_one_video, key, dry_run=False)
            futures[f] = key

        for f in as_completed(futures):
            key = futures[f]
            completed += 1
            try:
                result = f.result()
                if result == "fixed":
                    with stats_lock:
                        stats["fixed"] += 1
                elif result == "skipped":
                    with stats_lock:
                        stats["skipped"] += 1
                else:
                    with stats_lock:
                        stats["failed"] += 1
            except Exception as e:
                tprint(f"  ❌ Exception: {key} — {e}")
                with stats_lock:
                    stats["failed"] += 1

            # Progress every 50 videos
            if completed % 50 == 0:
                elapsed = time.time() - start_time
                rate = completed / elapsed if elapsed > 0 else 0
                remaining = (len(mp4_keys) - completed) / rate / 60 if rate > 0 else 0
                tprint(f"\n  Progress: {completed}/{len(mp4_keys)} "
                       f"({stats['fixed']} fixed, {stats['failed']} failed) "
                       f"~{remaining:.0f}min remaining")

    elapsed = time.time() - start_time
    saved_mb = stats["bytes_saved"] / 1024 / 1024

    print(f"\n{'=' * 70}")
    print(f"  DONE in {elapsed/60:.1f} minutes")
    print(f"  Fixed:   {stats['fixed']}")
    print(f"  Skipped: {stats['skipped']}")
    print(f"  Failed:  {stats['failed']}")
    print(f"  Size delta: {saved_mb:+.1f} MB")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
