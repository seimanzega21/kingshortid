#!/usr/bin/env python3
"""
TURBO upload for CRITICAL dramas — processes 3 dramas in parallel,
each with 20 upload workers = 60 concurrent uploads.
Checks R2 first, only uploads missing files.
"""
import boto3, os, json
from pathlib import Path
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading, time

load_dotenv()

# Create separate S3 clients for each thread pool to avoid connection issues
def make_s3():
    return boto3.client('s3',
        endpoint_url=os.getenv('R2_ENDPOINT'),
        aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
        region_name='auto'
    )

BUCKET = 'shortlovers'
LOCAL_DIR = Path('r2_ready/melolo')
WORKERS_PER_DRAMA = 20
PARALLEL_DRAMAS = 3

CT = {
    '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp',
    '.json': 'application/json', '.m3u8': 'application/vnd.apple.mpegurl',
    '.ts': 'video/mp2t', '.mp4': 'video/mp4',
}

stats = {'uploaded': 0, 'skipped': 0, 'failed': 0, 'dramas_done': 0, 'dramas_skipped': 0}
lock = threading.Lock()

def get_existing_keys(s3, prefix):
    keys = set()
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=BUCKET, Prefix=prefix):
        for obj in page.get('Contents', []):
            keys.add(obj['Key'])
    return keys

def upload_file(args):
    local_path, r2_key, s3 = args
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

def process_drama(slug, idx, total):
    """Upload only MISSING files for a drama"""
    s3 = make_s3()
    drama_dir = LOCAL_DIR / slug
    
    if not drama_dir.exists():
        print(f"  [{idx}/{total}] {slug}: ⚠️ Not found locally")
        return
    
    # Check R2
    existing = get_existing_keys(s3, f"melolo/{slug}/")
    
    # Collect local files
    all_files = []
    for fp in drama_dir.rglob('*'):
        if fp.is_file():
            rk = f"melolo/{slug}/{fp.relative_to(drama_dir).as_posix()}"
            all_files.append((fp, rk))
    
    missing = [(fp, rk) for fp, rk in all_files if rk not in existing]
    
    if not missing:
        with lock:
            stats['dramas_skipped'] += 1
        print(f"  [{idx}/{total}] {slug}: ✅ Complete ({len(existing)} files)")
        return
    
    print(f"  [{idx}/{total}] {slug}: ⬆️ {len(missing)} missing / {len(all_files)} total")
    
    start = time.time()
    done = [0]
    
    with ThreadPoolExecutor(max_workers=WORKERS_PER_DRAMA) as ex:
        tasks = [(fp, rk, s3) for fp, rk in missing]
        futures = [ex.submit(upload_file, t) for t in tasks]
        for f in as_completed(futures):
            done[0] += 1
            if done[0] % 300 == 0:
                elapsed = time.time() - start
                rate = done[0] / elapsed
                print(f"    [{idx}/{total}] {slug}: {done[0]}/{len(missing)} ({rate:.0f}/s)")
    
    elapsed = time.time() - start
    rate = len(missing) / elapsed if elapsed > 0 else 0
    with lock:
        stats['dramas_done'] += 1
    print(f"  [{idx}/{total}] {slug}: ✅ {len(missing)} uploaded in {elapsed:.0f}s ({rate:.1f}/s)")

# Main
print("=" * 70)
print(f"  TURBO UPLOAD: {PARALLEL_DRAMAS} dramas × {WORKERS_PER_DRAMA} workers = {PARALLEL_DRAMAS * WORKERS_PER_DRAMA} concurrent")
print("=" * 70)

with open('r2_validation_report.json', 'r', encoding='utf-8') as f:
    report = json.load(f)

critical = [d for d in report['dramas'] if d['status'] == 'CRITICAL']
print(f"\n  {len(critical)} critical dramas to process\n")

start_total = time.time()

# Process dramas in parallel batches
with ThreadPoolExecutor(max_workers=PARALLEL_DRAMAS) as drama_pool:
    futures = []
    for i, drama in enumerate(critical):
        f = drama_pool.submit(process_drama, drama['slug'], i+1, len(critical))
        futures.append(f)
    
    for f in as_completed(futures):
        try:
            f.result()
        except Exception as e:
            print(f"  ❌ Error: {e}")

elapsed_total = time.time() - start_total

print("\n" + "=" * 70)
print("  TURBO UPLOAD COMPLETE!")
print("=" * 70)
print(f"  Dramas uploaded:  {stats['dramas_done']}")
print(f"  Dramas skipped:   {stats['dramas_skipped']} (already complete)")
print(f"  Files uploaded:   {stats['uploaded']}")
print(f"  Files failed:     {stats['failed']}")
print(f"  Total time:       {elapsed_total/60:.1f} min")
print(f"  Avg speed:        {stats['uploaded']/elapsed_total:.1f} files/s" if elapsed_total > 0 else "")
print("=" * 70)
