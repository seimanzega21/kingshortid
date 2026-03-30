#!/usr/bin/env python3
"""Delete uncompressed (faststart-only) drama folders from R2 so v3 can re-process them."""
import os, boto3
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client("s3",
    endpoint_url=os.getenv("R2_ENDPOINT"),
    aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
    region_name="auto",
)

BUCKET = os.getenv("R2_BUCKET_NAME")

# Slugs dari 5 drama yang diproses faststart-only (tanpa kompresi)
UNCOMPRESSED_SLUGS = [
    "madam-pulang-menantu-ditolak",
    "rahasia-pemandian-air-panas",
    "maaf-aku-memang-ratu-utamanya",
    "tuan-serigala-jangan-makan-aku",
    "kembalinya-sang-master-kartu",
]

PREFIX = "dramas/microdrama"

for slug in UNCOMPRESSED_SLUGS:
    folder = f"{PREFIX}/{slug}/"
    print(f"\nDeleting R2 folder: {folder}")
    paginator = s3.get_paginator("list_objects_v2")
    deleted = 0
    for page in paginator.paginate(Bucket=BUCKET, Prefix=folder):
        objects = page.get("Contents", [])
        if not objects:
            print(f"  (empty or not found)")
            continue
        delete_keys = [{"Key": obj["Key"]} for obj in objects]
        s3.delete_objects(Bucket=BUCKET, Delete={"Objects": delete_keys})
        deleted += len(delete_keys)
        print(f"  Deleted {deleted} objects so far...")
    if deleted > 0:
        print(f"  ✅ Done: {deleted} objects deleted")
    else:
        print(f"  ⚠️  Nothing found for {slug}")

print("\n✅ Cleanup complete. Now run vidrama_microdrama_mp4_v3.py to re-process with compression.")
