#!/usr/bin/env python3
"""
R2 MP4 COMPRESS RETRY (v2)
==========================
Re-compress MP4 di R2 yang belum dioptimasi untuk mobile/4G.

Smart skipping:
  - File < 12MB → skip (sudah compressed)
  - File > 80MB → skip faststart-only (terlalu besar untuk re-encode lokal)
  - File 12-80MB → full re-encode (CRF 26 + faststart)

Bug fix dari script lama:
  - Pakai PID+hash sebagai nama temp file (fix WinError 32 file lock)
  - Timeout 600s untuk video besar (up dari 300s)

Usage:
    python r2_compress_retry.py              # dry-run (list video yang perlu diproses)
    python r2_compress_retry.py --apply      # apply ke semua
    python r2_compress_retry.py --apply --limit 100   # limit 100 file
    python r2_compress_retry.py --apply --drama legenda-naga  # filter drama tertentu
    python r2_compress_retry.py --apply --min-size 15  # skip file < 15MB (default: 12)
"""
import boto3, os, sys, subprocess, time, hashlib
from pathlib import Path
from dotenv import load_dotenv

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

load_dotenv()

R2_BUCKET  = os.getenv("R2_BUCKET_NAME") or "shortlovers"
R2_PREFIX  = "dramas/"
TEMP_DIR   = Path("C:/tmp/compress_retry")

DRY_RUN      = "--apply" not in sys.argv
LIMIT        = None
DRAMA_FILTER = None
MIN_SIZE_MB  = 12.0  # skip file di bawah ini (already compressed)
MAX_ENCODE_MB = 80.0  # di atas ini → faststart-only, tidak re-encode

if "--limit" in sys.argv:
    idx = sys.argv.index("--limit")
    if idx + 1 < len(sys.argv):
        LIMIT = int(sys.argv[idx + 1])

if "--drama" in sys.argv:
    idx = sys.argv.index("--drama")
    if idx + 1 < len(sys.argv):
        DRAMA_FILTER = sys.argv[idx + 1]

if "--min-size" in sys.argv:
    idx = sys.argv.index("--min-size")
    if idx + 1 < len(sys.argv):
        MIN_SIZE_MB = float(sys.argv[idx + 1])

# Unique prefix per process (fix WinError 32)
PID_PREFIX = f"pid{os.getpid()}"


def get_s3():
    return boto3.client("s3",
        endpoint_url=os.getenv("R2_ENDPOINT"),
        aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
        region_name="auto",
    )


def check_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
        return True
    except:
        print("❌ ffmpeg not found. Install: winget install Gyan.FFmpeg")
        return False


def faststart_only(src: Path, dst: Path) -> bool:
    """Hanya pindahkan moov atom (tanpa re-encode). Cepat, tidak lossy."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", str(src),
             "-c", "copy", "-movflags", "+faststart", str(dst)],
            capture_output=True, timeout=180
        )
        return result.returncode == 0 and dst.exists() and dst.stat().st_size > 1000
    except Exception as e:
        print(f"  ffmpeg error (faststart-only): {e}")
        return False


def full_compress(src: Path, dst: Path, size_mb: float) -> bool:
    """Re-encode dengan CRF 26 + faststart. Optimal untuk 4G streaming."""
    # Timeout proporsional dengan ukuran (60s per 10MB, min 120s, max 600s)
    timeout = max(120, min(600, int(size_mb * 6)))
    try:
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", str(src),
             "-c:v", "libx264", "-crf", "26", "-preset", "fast",
             "-maxrate", "1500k", "-bufsize", "3000k",
             "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
             "-movflags", "+faststart",
             str(dst)],
            capture_output=True, timeout=timeout
        )
        if result.returncode == 0 and dst.exists() and dst.stat().st_size > 1000:
            return True

        # Fallback: faststart only
        print(f"    [FALLBACK] full encode gagal (rc={result.returncode}), coba faststart-only...")
        return faststart_only(src, dst)
    except subprocess.TimeoutExpired:
        print(f"    [TIMEOUT] encode timeout {timeout}s, coba faststart-only...")
        return faststart_only(src, dst)
    except Exception as e:
        print(f"  ffmpeg error: {e}")
        return False


def main():
    if not check_ffmpeg():
        return

    s3 = get_s3()
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    mode = "DRY-RUN" if DRY_RUN else "APPLYING"
    print(f"=== R2 Compress Retry v2 [{mode}] ===")
    print(f"Bucket   : {R2_BUCKET}, Prefix: {R2_PREFIX}")
    print(f"Skip file < {MIN_SIZE_MB}MB (already optimal)")
    print(f"Faststart-only file > {MAX_ENCODE_MB}MB")
    if DRAMA_FILTER:
        print(f"Filter   : drama mengandung '{DRAMA_FILTER}'")
    if LIMIT:
        print(f"Limit    : {LIMIT} file")
    if DRY_RUN:
        print("\n⚠️  Dry run mode. Gunakan --apply untuk proses file.\n")

    paginator = s3.get_paginator("list_objects_v2")
    stats = {"total": 0, "need_compress": 0, "fixed": 0, "skipped_small": 0, "error": 0}
    processed = 0

    for page in paginator.paginate(Bucket=R2_BUCKET, Prefix=R2_PREFIX):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if not key.endswith(".mp4"):
                continue

            # Drama filter
            if DRAMA_FILTER and DRAMA_FILTER not in key:
                continue

            stats["total"] += 1
            size_mb = obj["Size"] / 1024 / 1024

            # Skip jika sudah kecil (sudah tercompress)
            if size_mb < MIN_SIZE_MB:
                stats["skipped_small"] += 1
                continue

            stats["need_compress"] += 1

            if LIMIT and processed >= LIMIT:
                break

            action = "faststart-only" if size_mb > MAX_ENCODE_MB else f"re-encode+faststart"
            print(f"  [{stats['need_compress']}] {key} ({size_mb:.1f}MB) → {action}")

            if DRY_RUN:
                continue

            # Unique temp file names per process + key hash (fix WinError 32)
            fhash = hashlib.md5(key.encode()).hexdigest()[:8]
            raw  = TEMP_DIR / f"{PID_PREFIX}_raw_{fhash}.mp4"
            fast = TEMP_DIR / f"{PID_PREFIX}_fast_{fhash}.mp4"

            try:
                print(f"    Downloading...")
                s3.download_file(R2_BUCKET, key, str(raw))

                if size_mb > MAX_ENCODE_MB:
                    ok = faststart_only(raw, fast)
                else:
                    ok = full_compress(raw, fast, size_mb)

                if not ok:
                    print(f"    [FAIL] ffmpeg gagal")
                    stats["error"] += 1
                    continue

                new_size = fast.stat().st_size / 1024 / 1024
                ratio = (1 - new_size / size_mb) * 100 if size_mb > 0 else 0
                print(f"    Compressed: {size_mb:.1f}MB → {new_size:.1f}MB ({ratio:.0f}% smaller)")

                print(f"    Uploading...")
                with open(fast, 'rb') as fh:
                    data = fh.read()

                s3.put_object(
                    Bucket=R2_BUCKET,
                    Key=key,
                    Body=data,
                    ContentType='video/mp4',
                    CacheControl='public, max-age=31536000, immutable',
                    ContentDisposition='inline',
                )
                stats["fixed"] += 1
                processed += 1
                print(f"    [OK] Uploaded {new_size:.1f}MB")

            except Exception as e:
                print(f"    [ERR] {e}")
                stats["error"] += 1
            finally:
                for f in [raw, fast]:
                    try: f.unlink(missing_ok=True)
                    except: pass

            time.sleep(0.3)

        if LIMIT and processed >= LIMIT:
            break

    # Cleanup temp dir jika kosong
    try: TEMP_DIR.rmdir()
    except: pass

    print(f"\n=== HASIL ===")
    print(f"Total MP4       : {stats['total']}")
    print(f"Sudah optimal   : {stats['skipped_small']} (< {MIN_SIZE_MB}MB)")
    print(f"Perlu diproses  : {stats['need_compress']}")
    if not DRY_RUN:
        print(f"Berhasil difix  : {stats['fixed']}")
        print(f"Error           : {stats['error']}")
    else:
        print(f"\nJalankan --apply untuk compress {stats['need_compress']} file yang perlu diproses.")
        est_min = stats['need_compress'] * 1.5  # ~1.5 menit per file
        print(f"Estimasi waktu  : {est_min/60:.0f} jam {est_min%60:.0f} menit")


if __name__ == "__main__":
    main()
