"""
Cleanup script: Delete all Meloshort dramas from D1 database and R2 storage.
"""
import requests
import json
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

WORKER_API = "https://api.shortlovers.id/api"
R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "kingshort-videos")


def get_r2_client():
    return boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name="auto",
    )


def find_meloshort_dramas():
    """Find all dramas with meloshort in cover URL."""
    meloshort = []
    page = 1
    while True:
        r = requests.get(
            f"{WORKER_API}/dramas",
            params={"includeInactive": "true", "limit": 50, "page": page},
            timeout=15,
        )
        data = r.json()
        dramas = data.get("dramas", [])
        if not dramas:
            break
        for d in dramas:
            cover = (d.get("cover") or "").lower()
            if "meloshort" in cover:
                meloshort.append(d)
        if len(dramas) < 50:
            break
        page += 1
    return meloshort


def delete_drama_from_d1(drama_id, title):
    """Delete a drama and all its episodes from D1 via Worker API."""
    r = requests.delete(f"{WORKER_API}/dramas/{drama_id}", timeout=15)
    if r.status_code == 200:
        print(f"  [DB] Deleted: {title} ({drama_id})")
        return True
    else:
        print(f"  [DB] FAILED to delete {title}: {r.status_code} {r.text[:100]}")
        return False


def delete_r2_folder(prefix):
    """Delete all objects in R2 with the given prefix."""
    s3 = get_r2_client()
    deleted = 0
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=R2_BUCKET_NAME, Prefix=prefix):
        objects = page.get("Contents", [])
        if not objects:
            break
        delete_keys = [{"Key": obj["Key"]} for obj in objects]
        s3.delete_objects(
            Bucket=R2_BUCKET_NAME, Delete={"Objects": delete_keys}
        )
        deleted += len(delete_keys)
    return deleted


def main():
    print("=" * 60)
    print("MELOSHORT CLEANUP")
    print("=" * 60)

    # Step 1: Find all Meloshort dramas
    print("\n[1] Finding Meloshort dramas in D1...")
    dramas = find_meloshort_dramas()
    print(f"    Found {len(dramas)} Meloshort dramas")
    for d in dramas:
        print(f"    - {d['title']} ({d['id'][:20]}...)")

    if not dramas:
        print("\n    No Meloshort dramas found. Nothing to clean.")
        return

    # Step 2: Delete dramas from D1
    print(f"\n[2] Deleting {len(dramas)} dramas from D1 database...")
    deleted_db = 0
    for d in dramas:
        if delete_drama_from_d1(d["id"], d["title"]):
            deleted_db += 1

    # Step 3: Delete R2 files
    print("\n[3] Deleting Meloshort files from R2...")
    r2_prefix = "dramas/meloshort/"
    deleted_r2 = delete_r2_folder(r2_prefix)
    print(f"  [R2] Deleted {deleted_r2} objects from {r2_prefix}")

    # Step 4: Clean up local files
    print("\n[4] Cleaning up local temp files...")
    import shutil
    temp_dir = os.path.join(os.path.dirname(__file__), "temp_downloads")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        print(f"  Removed {temp_dir}")
    
    state_file = os.path.join(os.path.dirname(__file__), "meloshort_state.json")
    if os.path.exists(state_file):
        os.remove(state_file)
        print(f"  Removed {state_file}")

    # Summary
    print("\n" + "=" * 60)
    print("CLEANUP COMPLETE")
    print(f"  D1 dramas deleted: {deleted_db}/{len(dramas)}")
    print(f"  R2 objects deleted: {deleted_r2}")
    print("=" * 60)


if __name__ == "__main__":
    main()
