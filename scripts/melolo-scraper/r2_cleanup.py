#!/usr/bin/env python3
"""
R2 Bucket Cleanup:
1. Abort ALL stuck multipart uploads
2. Audit root-level directories (old format slugs)
"""
import boto3, os, sys
from dotenv import load_dotenv

load_dotenv()
sys.stdout.reconfigure(encoding="utf-8")

s3 = boto3.client("s3",
    endpoint_url=os.getenv("R2_ENDPOINT"),
    aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
    region_name="auto",
)
BUCKET = os.getenv("R2_BUCKET_NAME") or "shortlovers"

# ── 1. LIST & ABORT STUCK MULTIPART UPLOADS ──────────────
print("=" * 60)
print("[1] Checking stuck multipart uploads...")
total_aborted = 0

paginator = s3.get_paginator("list_multipart_uploads")
try:
    for page in paginator.paginate(Bucket=BUCKET):
        uploads = page.get("Uploads", [])
        if not uploads:
            print("    No stuck uploads found.")
            break
        for upload in uploads:
            key = upload["Key"]
            uid = upload["UploadId"]
            initiated = upload["Initiated"].strftime("%Y-%m-%d %H:%M")
            print(f"    ABORT: {key} (initiated {initiated})")
            s3.abort_multipart_upload(Bucket=BUCKET, Key=key, UploadId=uid)
            total_aborted += 1
except Exception as e:
    print(f"    Error: {e}")

print(f"    Aborted: {total_aborted} stuck uploads")

# ── 2. AUDIT ROOT-LEVEL DIRECTORIES ──────────────────────
print()
print("[2] Auditing root-level directories...")

pag = s3.get_paginator("list_objects_v2")
root_dirs = []
for page in pag.paginate(Bucket=BUCKET, Delimiter="/"):
    for p in page.get("CommonPrefixes", []):
        prefix = p["Prefix"].rstrip("/")
        root_dirs.append(prefix)

print(f"    Root-level prefixes: {len(root_dirs)}")
print()

# Categorize
known_prefixes = {"melolo", "dramas"}
legacy_dirs = []
for d in sorted(root_dirs):
    if d in known_prefixes:
        print(f"    [OK     ] {d}/")
    elif d.startswith("[") or "_" in d or d[0].isupper():
        # Legacy old-format directories
        legacy_dirs.append(d)
        print(f"    [LEGACY ] {d}/")
    else:
        print(f"    [UNKNOWN] {d}/")

print()
print(f"    Legacy dirs to delete: {len(legacy_dirs)}")
if legacy_dirs:
    print()
    print("    To delete these legacy dirs, run:")
    print("      python r2_cleanup.py --delete-legacy")

# ── 3. OPTIONAL: DELETE LEGACY DIRS ──────────────────────
if "--delete-legacy" in sys.argv and legacy_dirs:
    print()
    print("[3] Deleting legacy directories...")
    for prefix in legacy_dirs:
        # List and delete all objects under prefix
        count = 0
        objects_to_delete = []
        for page in pag.paginate(Bucket=BUCKET, Prefix=f"{prefix}/"):
            for obj in page.get("Contents", []):
                objects_to_delete.append({"Key": obj["Key"]})
                count += 1
                if len(objects_to_delete) >= 1000:
                    s3.delete_objects(Bucket=BUCKET,
                                      Delete={"Objects": objects_to_delete, "Quiet": True})
                    objects_to_delete = []
        if objects_to_delete:
            s3.delete_objects(Bucket=BUCKET,
                              Delete={"Objects": objects_to_delete, "Quiet": True})
        print(f"    DELETED: {prefix}/ ({count} objects)")
    print("    Legacy cleanup complete!")

print()
print("Done.")
