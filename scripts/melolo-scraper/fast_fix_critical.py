#!/usr/bin/env python3
"""
SMART upload for CRITICAL dramas - checks R2 first, only uploads missing files.
Skips dramas that already have episodes on R2.
"""
import boto3, os, json
from pathlib import Path
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading, time

load_dotenv()

s3 = boto3.client('s3',
    endpoint_url=os.getenv('R2_ENDPOINT'),
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
    region_name='auto'
)

BUCKET = 'shortlovers'
LOCAL_DIR = Path('r2_ready/melolo')
WORKERS = 15

CT = {
    '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp',
    '.json': 'application/json', '.m3u8': 'application/vnd.apple.mpegurl',
    '.ts': 'video/mp2t', '.mp4': 'video/mp4',
}

stats = {'uploaded': 0, 'skipped': 0, 'failed': 0}
lock = threading.Lock()

def get_existing_keys(prefix):
    """List all existing keys on R2 for a prefix"""
    keys = set()
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=BUCKET, Prefix=prefix):
        for obj in page.get('Contents', []):
            keys.add(obj['Key'])
    return keys

def upload_file(args):
    local_path, r2_key = args
    ct = CT.get(local_path.suffix.lower(), 'application/octet-stream')
    try:
        s3.upload_file(str(local_path), BUCKET, r2_key, ExtraArgs={'ContentType': ct})
        with lock:
            stats['uploaded'] += 1
        return True
    except Exception:
        with lock:
            stats['failed'] += 1
        return False

def upload_drama(slug):
    """Upload only MISSING files for a drama"""
    drama_dir = LOCAL_DIR / slug
    if not drama_dir.exists():
        print(f"  ⚠️  Not found locally")
        return 0, 0

    # Check what already exists on R2
    print(f"  Checking R2...")
    existing = get_existing_keys(f"melolo/{slug}/")
    
    # Collect local files
    all_tasks = []
    for file_path in drama_dir.rglob('*'):
        if not file_path.is_file():
            continue
        rel_path = file_path.relative_to(LOCAL_DIR / slug)
        r2_key = f"melolo/{slug}/{rel_path.as_posix()}"
        all_tasks.append((file_path, r2_key))

    # Filter out already uploaded
    missing = [(fp, rk) for fp, rk in all_tasks if rk not in existing]
    
    if not missing:
        print(f"  ✅ Already complete on R2 ({len(existing)} files)")
        return 0, len(existing)
    
    print(f"  {len(missing)}/{len(all_tasks)} files missing (R2 has {len(existing)})")
    
    # Upload only missing files
    done = [0]
    start = time.time()
    
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futures = [ex.submit(upload_file, t) for t in missing]
        for f in as_completed(futures):
            done[0] += 1
            if done[0] % 200 == 0:
                elapsed = time.time() - start
                rate = done[0] / elapsed
                print(f"    {done[0]}/{len(missing)} uploaded ({rate:.0f}/s)")

    elapsed = time.time() - start
    print(f"  ✅ {len(missing)} files uploaded in {elapsed:.0f}s (skipped {len(existing)})")
    return len(missing), len(existing)

# Main
print("=" * 70)
print("  SMART UPLOAD: CRITICAL DRAMAS (skip existing)")
print("=" * 70)

with open('r2_validation_report.json', 'r', encoding='utf-8') as f:
    report = json.load(f)

critical = [d for d in report['dramas'] if d['status'] == 'CRITICAL']
print(f"\n  {len(critical)} critical dramas to check\n")

start_total = time.time()
dramas_uploaded = 0
dramas_skipped = 0

for i, drama in enumerate(critical):
    slug = drama['slug']
    print(f"\n[{i+1}/{len(critical)}] {slug}")
    uploaded, existing = upload_drama(slug)
    if uploaded > 0:
        dramas_uploaded += 1
    elif existing > 0:
        dramas_skipped += 1

elapsed_total = time.time() - start_total

print("\n" + "=" * 70)
print("  COMPLETE!")
print("=" * 70)
print(f"  Dramas uploaded:  {dramas_uploaded}")
print(f"  Dramas skipped:   {dramas_skipped}")
print(f"  Files uploaded:   {stats['uploaded']}")
print(f"  Files skipped:    {stats['skipped']}")
print(f"  Files failed:     {stats['failed']}")
print(f"  Total time:       {elapsed_total/60:.1f} min")
print("=" * 70)
