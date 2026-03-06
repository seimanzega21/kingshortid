#!/usr/bin/env python3
"""
R2 CACHE-CONTROL BACKFILL
==========================
Adds Cache-Control: public, max-age=31536000, immutable to all existing
video files in R2 (mp4, ts, m3u8, webp) that don't have it yet.

This is a one-time fix. Run once to make Cloudflare cache all existing videos
at edge nodes, so users on mobile data get faster video loading.

Usage:
    python r2_set_cache_control.py              # dry-run (no changes)
    python r2_set_cache_control.py --apply      # apply cache headers
    python r2_set_cache_control.py --apply --prefix dramas/microdrama  # specific folder
"""
import boto3, os, sys, time
from dotenv import load_dotenv

load_dotenv()

R2_BUCKET = os.getenv("R2_BUCKET_NAME") or "shortlovers"
DRY_RUN   = "--apply" not in sys.argv

# File type → Cache-Control value
CACHE_RULES = {
    ".mp4":   ("video/mp4",                        "public, max-age=31536000, immutable"),
    ".ts":    ("video/MP2T",                       "public, max-age=31536000, immutable"),
    ".m3u8":  ("application/vnd.apple.mpegurl",    "public, max-age=31536000, immutable"),
    ".webp":  ("image/webp",                       "public, max-age=86400"),
    ".jpg":   ("image/jpeg",                       "public, max-age=86400"),
    ".png":   ("image/png",                        "public, max-age=86400"),
}

PREFIX = "dramas/"
for arg in sys.argv:
    if arg.startswith("--prefix"):
        idx = sys.argv.index(arg)
        if idx + 1 < len(sys.argv):
            PREFIX = sys.argv[idx + 1]

def get_s3():
    return boto3.client("s3",
        endpoint_url=os.getenv("R2_ENDPOINT"),
        aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
        region_name="auto",
    )

def main():
    s3 = get_s3()
    mode = "DRY-RUN" if DRY_RUN else "APPLYING"
    print(f"=== R2 Cache-Control Backfill [{mode}] ===")
    print(f"Bucket: {R2_BUCKET}, Prefix: {PREFIX}")
    print()

    paginator = s3.get_paginator("list_objects_v2")
    stats = {"total": 0, "updated": 0, "skipped": 0, "error": 0}

    for page in paginator.paginate(Bucket=R2_BUCKET, Prefix=PREFIX):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            ext = "." + key.rsplit(".", 1)[-1].lower() if "." in key else ""

            if ext not in CACHE_RULES:
                continue

            stats["total"] += 1
            content_type, cache_control = CACHE_RULES[ext]

            # Check current metadata
            try:
                head = s3.head_object(Bucket=R2_BUCKET, Key=key)
                current_cc = head.get("CacheControl", "")
                if "max-age=31536000" in current_cc or "max-age=86400" in current_cc:
                    stats["skipped"] += 1
                    continue
            except Exception as e:
                print(f"  HEAD error {key}: {e}")
                stats["error"] += 1
                continue

            print(f"  {'WOULD UPDATE' if DRY_RUN else 'UPDATING'}: {key}")

            if not DRY_RUN:
                try:
                    # Copy object to itself with new metadata
                    s3.copy_object(
                        Bucket=R2_BUCKET,
                        CopySource={"Bucket": R2_BUCKET, "Key": key},
                        Key=key,
                        ContentType=content_type,
                        CacheControl=cache_control,
                        MetadataDirective="REPLACE",
                    )
                    stats["updated"] += 1
                    time.sleep(0.05)  # rate limit
                except Exception as e:
                    print(f"  ERROR: {key}: {e}")
                    stats["error"] += 1
            else:
                stats["updated"] += 1

    print(f"\n=== RESULTS ===")
    print(f"Total files  : {stats['total']}")
    print(f"Would update : {stats['updated']}" if DRY_RUN else f"Updated      : {stats['updated']}")
    print(f"Already OK   : {stats['skipped']}")
    print(f"Errors       : {stats['error']}")

    if DRY_RUN and stats["updated"] > 0:
        print(f"\nRun with --apply to apply changes.")

if __name__ == "__main__":
    main()
