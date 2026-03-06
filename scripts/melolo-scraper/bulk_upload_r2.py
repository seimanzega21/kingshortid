#!/usr/bin/env python3
"""
Bulk upload ALL existing r2_ready/melolo data to R2.
Runs alongside the scraping pipeline — skips dramas already fully on R2.
Uses threading for parallel uploads.
"""
import json, sys, io, os, time, boto3
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
import threading

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stdout.reconfigure(line_buffering=True)

load_dotenv(Path(__file__).parent / '.env')

R2_ENDPOINT = os.getenv('R2_ENDPOINT')
R2_ACCESS_KEY_ID = os.getenv('R2_ACCESS_KEY_ID')
R2_SECRET_ACCESS_KEY = os.getenv('R2_SECRET_ACCESS_KEY')
R2_BUCKET = os.getenv('R2_BUCKET_NAME', 'shortlovers')

MELOLO_DIR = Path(__file__).parent / 'r2_ready' / 'melolo'

CONTENT_TYPES = {
    '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp',
    '.json': 'application/json', '.m3u8': 'application/vnd.apple.mpegurl',
    '.ts': 'video/mp2t', '.mp4': 'video/mp4',
}

print_lock = threading.Lock()
stats_lock = threading.Lock()
stats = {'uploaded': 0, 'skipped': 0, 'errors': 0, 'bytes': 0, 'dramas_done': 0}


def safe_print(*args, **kwargs):
    with print_lock:
        print(*args, **kwargs, flush=True)


def get_r2_client():
    return boto3.client('s3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name='auto'
    )


def get_r2_existing_keys(s3, prefix):
    """List all existing keys under a prefix on R2"""
    existing = set()
    paginator = s3.get_paginator('list_objects_v2')
    try:
        for page in paginator.paginate(Bucket=R2_BUCKET, Prefix=prefix):
            for obj in page.get('Contents', []):
                existing.add(obj['Key'])
    except:
        pass
    return existing


def upload_drama(drama_dir):
    """Upload a single drama folder to R2, skipping files already uploaded"""
    slug = drama_dir.name
    r2_prefix = f"melolo/{slug}"
    
    # Get own S3 client (thread-safe)
    s3 = get_r2_client()
    
    # Check what's already on R2
    existing_keys = get_r2_existing_keys(s3, r2_prefix + '/')
    
    # Get all local files
    local_files = [f for f in sorted(drama_dir.rglob('*')) if f.is_file() and f.stat().st_size > 0]
    
    uploaded = 0
    skipped = 0
    errors = 0
    total_bytes = 0
    
    for fpath in local_files:
        rel = fpath.relative_to(drama_dir)
        r2_key = f"{r2_prefix}/{rel.as_posix()}"
        
        if r2_key in existing_keys:
            skipped += 1
            continue
        
        ct = CONTENT_TYPES.get(fpath.suffix.lower(), 'application/octet-stream')
        try:
            s3.upload_file(str(fpath), R2_BUCKET, r2_key, ExtraArgs={'ContentType': ct})
            uploaded += 1
            total_bytes += fpath.stat().st_size
        except Exception as e:
            errors += 1
    
    with stats_lock:
        stats['uploaded'] += uploaded
        stats['skipped'] += skipped
        stats['errors'] += errors
        stats['bytes'] += total_bytes
        stats['dramas_done'] += 1
    
    return slug, uploaded, skipped, errors, total_bytes


def main():
    print("=" * 60)
    print("  BULK UPLOAD ALL MELOLO DATA TO R2")
    print("=" * 60)
    
    # Connect to R2
    s3 = get_r2_client()
    s3.head_bucket(Bucket=R2_BUCKET)
    print(f"\n✅ R2 connected: {R2_BUCKET}")
    
    # Get all drama dirs with content
    drama_dirs = []
    for d in sorted(MELOLO_DIR.iterdir()):
        if not d.is_dir():
            continue
        # Only include dramas that have some files
        files = list(d.rglob('*'))
        file_count = sum(1 for f in files if f.is_file())
        if file_count > 0:
            drama_dirs.append(d)
    
    print(f"  Found {len(drama_dirs)} dramas with content")
    
    num_workers = 6  # 6 upload workers
    print(f"  Using {num_workers} upload workers\n")
    
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = {executor.submit(upload_drama, d): d for d in drama_dirs}
        
        for future in as_completed(futures):
            try:
                slug, uploaded, skipped, errors, total_bytes = future.result()
                mb = total_bytes / (1024 * 1024)
                
                if uploaded > 0:
                    safe_print(f"  ✅ {slug}: {uploaded} uploaded ({mb:.1f}MB), {skipped} skipped")
                elif errors > 0:
                    safe_print(f"  ⚠ {slug}: {errors} errors, {skipped} skipped")
                else:
                    safe_print(f"  ⏭ {slug}: all {skipped} files already on R2")
                
                # Progress
                with stats_lock:
                    done = stats['dramas_done']
                
                if done % 10 == 0:
                    elapsed = time.time() - start_time
                    safe_print(f"\n  📊 Progress: {done}/{len(drama_dirs)} dramas | {stats['uploaded']} files | {stats['bytes']/(1024**3):.2f}GB | {elapsed:.0f}s\n")
                    
            except Exception as e:
                safe_print(f"  ❌ Error: {e}")
    
    elapsed = time.time() - start_time
    gb = stats['bytes'] / (1024 ** 3)
    
    print(f"\n{'=' * 60}")
    print(f"  BULK UPLOAD COMPLETE!")
    print(f"{'=' * 60}")
    print(f"  Dramas processed: {stats['dramas_done']}")
    print(f"  Files uploaded:   {stats['uploaded']}")
    print(f"  Files skipped:    {stats['skipped']} (already on R2)")
    print(f"  Errors:           {stats['errors']}")
    print(f"  Data uploaded:    {gb:.2f} GB")
    print(f"  Time elapsed:     {elapsed:.0f}s ({elapsed/60:.1f}min)")
    print(f"{'=' * 60}\n")


if __name__ == '__main__':
    main()
