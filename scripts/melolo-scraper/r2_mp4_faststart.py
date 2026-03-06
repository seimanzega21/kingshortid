#!/usr/bin/env python3
"""
MP4 FASTSTART BACKFILL
======================
Re-processes existing MP4 files in R2 to add faststart (moov atom at front).
This is the #1 fix for slow video start on mobile data.

Without faststart: player must download ENTIRE file before playing.
With faststart: player can start streaming after first few KB (metadata only).

Usage:
    python r2_mp4_faststart.py              # dry-run
    python r2_mp4_faststart.py --apply      # apply to all MP4s in R2
    python r2_mp4_faststart.py --apply --limit 50  # apply to first 50
"""
import boto3, os, sys, subprocess, tempfile, time
from pathlib import Path
from dotenv import load_dotenv

# Fix Windows cp1252 UnicodeEncodeError for emoji in print()
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

load_dotenv()

R2_BUCKET  = os.getenv("R2_BUCKET_NAME") or "shortlovers"
R2_PREFIX  = "dramas/"
TEMP_DIR   = Path("C:/tmp/faststart_backfill")
DRY_RUN    = "--apply" not in sys.argv
FORCE      = "--force" in sys.argv  # re-compress even if already faststart
LIMIT      = None
if "--limit" in sys.argv:
    idx = sys.argv.index("--limit")
    if idx + 1 < len(sys.argv):
        LIMIT = int(sys.argv[idx + 1])

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
        print("❌ ffmpeg not found. Install: winget install ffmpeg")
        return False

def is_faststart(path: Path) -> bool:
    """Check if MP4 already has moov atom at front using ffprobe."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "trace", "-i", str(path)],
            capture_output=True, text=True, timeout=10
        )
        output = result.stderr
        # moov before mdat = faststart
        moov_pos = output.find("moov")
        mdat_pos = output.find("mdat")
        if moov_pos > 0 and mdat_pos > 0:
            return moov_pos < mdat_pos
    except:
        pass
    return False  # assume not faststart if can't check

def apply_mobile_compress(src: Path, dst: Path) -> bool:
    """Re-encode with mobile-optimized settings + faststart.
    CRF 26 = good quality, ~800k-1.5Mbps → smooth on 4G data.
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-y", "-i", str(src),
             "-c:v", "libx264", "-crf", "26", "-preset", "fast",
             "-maxrate", "1500k", "-bufsize", "3000k",
             "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
             "-movflags", "+faststart",
             str(dst)],
            capture_output=True, timeout=300
        )
        if result.returncode == 0 and dst.exists() and dst.stat().st_size > 1000:
            return True
        # Fallback: faststart only (no quality loss, at least fix streaming)
        result2 = subprocess.run(
            ["ffmpeg", "-y", "-i", str(src),
             "-c", "copy", "-movflags", "+faststart", str(dst)],
            capture_output=True, timeout=120
        )
        return result2.returncode == 0 and dst.exists()
    except Exception as e:
        print(f"  ffmpeg error: {e}")
        return False

def main():
    if not check_ffmpeg():
        print("\nInstall ffmpeg first:\nwinget install Gyan.FFmpeg")
        return

    s3 = get_s3()
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    mode = "DRY-RUN" if DRY_RUN else "APPLYING"
    print(f"=== MP4 Faststart Backfill [{mode}] ===")
    print(f"Bucket: {R2_BUCKET}, Prefix: {R2_PREFIX}")

    if DRY_RUN:
        print("\n⚠️  Dry run. Use --apply to process files.\n")

    paginator = s3.get_paginator("list_objects_v2")
    stats = {"total": 0, "fixed": 0, "skip": 0, "error": 0}

    for page in paginator.paginate(Bucket=R2_BUCKET, Prefix=R2_PREFIX):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if not key.endswith(".mp4"):
                continue

            stats["total"] += 1

            if LIMIT and stats["fixed"] >= LIMIT:
                break

            size_mb = obj["Size"] / 1024 / 1024
            print(f"  [{stats['total']}] {key} ({size_mb:.1f}MB)")

            if DRY_RUN:
                stats["fixed"] += 1
                continue

            import hashlib
            fhash = hashlib.md5(key.encode()).hexdigest()[:8]
            raw  = TEMP_DIR / f"raw_{fhash}.mp4"
            fast = TEMP_DIR / f"fast_{fhash}.mp4"

            try:
                # Download from R2
                s3.download_file(R2_BUCKET, key, str(raw))

                # Check if already faststart (skip if --force)
                if not FORCE and is_faststart(raw):
                    print(f"    [OK] Already faststart, skipping")
                    stats["skip"] += 1
                    raw.unlink(missing_ok=True)
                    continue

                # Apply mobile compression + faststart
                if not apply_mobile_compress(raw, fast):
                    print(f"    [FAIL] ffmpeg failed")
                    stats["error"] += 1
                    raw.unlink(missing_ok=True)
                    fast.unlink(missing_ok=True)
                    continue

                new_size = fast.stat().st_size / 1024 / 1024
                print(f"    [DONE] compressed ({size_mb:.1f}MB -> {new_size:.1f}MB)")

                # Re-upload to R2 (put_object avoids Content-MD5 issues with R2)
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
                print(f"    [UP] Uploaded OK ({new_size:.1f}MB)")

            except Exception as e:
                print(f"    [ERR] Error: {e}")
                stats["error"] += 1
            finally:
                for f in [raw, fast]:
                    try: f.unlink()
                    except: pass

            time.sleep(0.2)  # gentle rate limit

    # Cleanup
    try: TEMP_DIR.rmdir()
    except: pass

    print(f"\n=== RESULTS ===")
    print(f"Total MP4s: {stats['total']}")
    if DRY_RUN:
        print(f"Would process: {stats['fixed']}")
    else:
        print(f"Fixed:        {stats['fixed']}")
        print(f"Already OK:   {stats['skip']}")
        print(f"Errors:       {stats['error']}")

    if DRY_RUN and stats["total"] > 0:
        print(f"\nRun with --apply to fix all {stats['total']} MP4 files.")
        print(f"Estimated time: {stats['total'] * 0.5:.0f}s - {stats['total'] * 2:.0f}s")

if __name__ == "__main__":
    main()
