#!/usr/bin/env python3
"""
R2 MP4 COMPRESS — PARALLEL (4 workers + ultrafast)
=====================================================
Encoding: libx264 -crf 26 -preset fast -maxrate 1500k
Speed comes from parallelism (4 workers), not lower quality.
Only uploads if result is SMALLER than original.
    python r2_compress_parallel.py              # dry-run
    python r2_compress_parallel.py --apply      # apply (4 workers)
    python r2_compress_parallel.py --apply --workers 6
    python r2_compress_parallel.py --apply --drama legenda-naga
    python r2_compress_parallel.py --apply --min-size 15
"""
import boto3, os, sys, subprocess, time, hashlib, threading
from pathlib import Path
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

load_dotenv()

R2_BUCKET     = os.getenv("R2_BUCKET_NAME") or "shortlovers"
R2_PREFIX     = "dramas/"
TEMP_DIR      = Path("C:/tmp/compress_parallel")
DRY_RUN       = "--apply" not in sys.argv
MIN_SIZE_MB   = 12.0
MAX_ENCODE_MB = 80.0
WORKERS       = 4

# Parse args
for flag, var_name in [("--workers", "WORKERS"), ("--min-size", "MIN_SIZE_MB")]:
    if flag in sys.argv:
        idx = sys.argv.index(flag)
        if idx + 1 < len(sys.argv):
            if var_name == "WORKERS":
                WORKERS = int(sys.argv[idx + 1])
            else:
                MIN_SIZE_MB = float(sys.argv[idx + 1])

DRAMA_FILTER = None
if "--drama" in sys.argv:
    idx = sys.argv.index("--drama")
    if idx + 1 < len(sys.argv):
        DRAMA_FILTER = sys.argv[idx + 1]

print_lock = threading.Lock()
stats_lock = threading.Lock()
stats = {"total": 0, "need": 0, "fixed": 0, "skipped": 0, "error": 0}


def log(msg):
    with print_lock:
        print(msg, flush=True)


def get_s3():
    return boto3.client("s3",
        endpoint_url=os.getenv("R2_ENDPOINT"),
        aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
        region_name="auto",
    )


def process_file(key, size_mb, worker_id):
    """Download → re-encode → upload one file."""
    s3 = get_s3()
    fhash = hashlib.md5(key.encode()).hexdigest()[:8]
    raw  = TEMP_DIR / f"w{worker_id}_raw_{fhash}.mp4"
    out  = TEMP_DIR / f"w{worker_id}_out_{fhash}.mp4"

    try:
        # Download
        log(f"  [W{worker_id}] ⬇ {key} ({size_mb:.1f}MB)")
        s3.download_file(R2_BUCKET, key, str(raw))

        # Encode
        if size_mb > MAX_ENCODE_MB:
            # Faststart only for huge files
            result = subprocess.run(
                ["ffmpeg", "-y", "-i", str(raw),
                 "-c", "copy", "-movflags", "+faststart", str(out)],
                capture_output=True, timeout=180
            )
        else:
            # Full re-encode with ultrafast preset
            timeout = max(90, min(600, int(size_mb * 4)))
            result = subprocess.run(
                ["ffmpeg", "-y", "-i", str(raw),
                 "-c:v", "libx264", "-crf", "26", "-preset", "fast",
                 "-maxrate", "1500k", "-bufsize", "3000k",
                 "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
                 "-movflags", "+faststart",
                 str(out)],
                capture_output=True, timeout=timeout
            )

        if result.returncode != 0 or not out.exists() or out.stat().st_size < 1000:
            # Fallback: faststart only
            result = subprocess.run(
                ["ffmpeg", "-y", "-i", str(raw),
                 "-c", "copy", "-movflags", "+faststart", str(out)],
                capture_output=True, timeout=180
            )
            if result.returncode != 0:
                log(f"  [W{worker_id}] ❌ FFmpeg failed: {key}")
                with stats_lock:
                    stats["error"] += 1
                return False

        new_mb = out.stat().st_size / 1024 / 1024
        pct = (1 - new_mb / size_mb) * 100 if size_mb > 0 else 0

        # CRITICAL: only upload if result is smaller
        if new_mb >= size_mb:
            log(f"  [W{worker_id}] ⏭ SKIP {key}: {size_mb:.1f}→{new_mb:.1f}MB (bigger, keeping original)")
            with stats_lock:
                stats["skipped"] += 1
            return True

        # Upload
        with open(out, 'rb') as fh:
            data = fh.read()

        s3.put_object(
            Bucket=R2_BUCKET,
            Key=key,
            Body=data,
            ContentType='video/mp4',
            CacheControl='public, max-age=31536000, immutable',
            ContentDisposition='inline',
        )

        with stats_lock:
            stats["fixed"] += 1

        log(f"  [W{worker_id}] ✅ {key}: {size_mb:.1f}→{new_mb:.1f}MB ({pct:.0f}% ↓)")
        return True

    except subprocess.TimeoutExpired:
        log(f"  [W{worker_id}] ⏰ Timeout: {key}")
        # Try faststart-only as fallback
        try:
            result = subprocess.run(
                ["ffmpeg", "-y", "-i", str(raw),
                 "-c", "copy", "-movflags", "+faststart", str(out)],
                capture_output=True, timeout=180
            )
            if result.returncode == 0 and out.exists():
                new_mb = out.stat().st_size / 1024 / 1024
                with open(out, 'rb') as fh:
                    s3.put_object(Bucket=R2_BUCKET, Key=key, Body=fh.read(),
                        ContentType='video/mp4',
                        CacheControl='public, max-age=31536000, immutable')
                with stats_lock:
                    stats["fixed"] += 1
                log(f"  [W{worker_id}] ⚡ Faststart-only: {key} ({new_mb:.1f}MB)")
                return True
        except:
            pass
        with stats_lock:
            stats["error"] += 1
        return False
    except Exception as e:
        log(f"  [W{worker_id}] ❌ {key}: {e}")
        with stats_lock:
            stats["error"] += 1
        return False
    finally:
        for f in [raw, out]:
            try: f.unlink(missing_ok=True)
            except: pass


def main():
    # Check ffmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
    except:
        print("❌ ffmpeg not found!")
        return

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    s3 = get_s3()

    mode = "DRY-RUN" if DRY_RUN else f"APPLYING ({WORKERS} workers)"
    print(f"=== R2 Parallel Compress [{mode}] ===")
    print(f"Bucket: {R2_BUCKET}, Prefix: {R2_PREFIX}")
    print(f"Skip < {MIN_SIZE_MB}MB | Faststart-only > {MAX_ENCODE_MB}MB")
    print(f"Encoding: libx264 -crf 26 -preset fast -maxrate 1500k")
    if DRAMA_FILTER:
        print(f"Filter: '{DRAMA_FILTER}'")
    if DRY_RUN:
        print("\n⚠️  Dry run. Use --apply to start.\n")

    # Collect all files first
    files_to_process = []
    paginator = s3.get_paginator("list_objects_v2")

    print("Scanning R2...", end="", flush=True)
    for page in paginator.paginate(Bucket=R2_BUCKET, Prefix=R2_PREFIX):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if not key.endswith(".mp4"):
                continue
            if DRAMA_FILTER and DRAMA_FILTER not in key:
                continue

            stats["total"] += 1
            size_mb = obj["Size"] / 1024 / 1024

            if size_mb < MIN_SIZE_MB:
                stats["skipped"] += 1
                continue

            files_to_process.append((key, size_mb))

    stats["need"] = len(files_to_process)
    print(f" found {stats['total']} MP4s, {stats['need']} need compression")

    if DRY_RUN:
        for i, (key, size_mb) in enumerate(files_to_process[:20], 1):
            action = "faststart-only" if size_mb > MAX_ENCODE_MB else "re-encode"
            print(f"  [{i}] {key} ({size_mb:.1f}MB) → {action}")
        if len(files_to_process) > 20:
            print(f"  ... and {len(files_to_process) - 20} more")
        est = len(files_to_process) * 0.5  # ~30s per file with ultrafast + parallel
        print(f"\nEstimasi: ~{est/60:.0f} jam {est%60:.0f} menit (parallel {WORKERS} workers)")
        return

    # Process with thread pool
    print(f"\n🚀 Starting {WORKERS} workers...\n")
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {}
        for i, (key, size_mb) in enumerate(files_to_process):
            worker_id = (i % WORKERS) + 1
            future = executor.submit(process_file, key, size_mb, worker_id)
            futures[future] = key

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                log(f"  ❌ Unexpected: {e}")

    elapsed = time.time() - start_time
    hours = int(elapsed // 3600)
    mins = int((elapsed % 3600) // 60)

    print(f"\n{'='*50}")
    print(f"  DONE in {hours}h {mins}m")
    print(f"  Total MP4    : {stats['total']}")
    print(f"  Skipped      : {stats['skipped']} (< {MIN_SIZE_MB}MB)")
    print(f"  Processed    : {stats['need']}")
    print(f"  ✅ Success   : {stats['fixed']}")
    print(f"  ❌ Errors    : {stats['error']}")
    print(f"{'='*50}")

    # Cleanup
    try: TEMP_DIR.rmdir()
    except: pass


if __name__ == "__main__":
    main()
