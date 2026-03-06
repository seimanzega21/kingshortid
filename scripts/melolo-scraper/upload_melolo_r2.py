#!/usr/bin/env python3
"""
MELOLO R2 UPLOADER
===================
Uploads melolo r2_ready HLS data (playlist.m3u8 + .ts segments) to Cloudflare R2.

Structure on R2:
  melolo/{drama-slug}/cover.jpg
  melolo/{drama-slug}/metadata.json
  melolo/{drama-slug}/ep001/playlist.m3u8
  melolo/{drama-slug}/ep001/seg_000.ts
  melolo/{drama-slug}/ep001/seg_001.ts
  ...

Usage:
    python upload_melolo_r2.py                   # Upload all incomplete
    python upload_melolo_r2.py --drama slug-name # Upload specific drama
    python upload_melolo_r2.py --list            # List uploadable dramas
"""

import boto3
import json
import os
import sys
import io
import time
from pathlib import Path
from dotenv import load_dotenv

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Load .env
SCRIPT_DIR = Path(__file__).parent
load_dotenv(SCRIPT_DIR / '.env')

# Config
R2_ENDPOINT = os.getenv("R2_ENDPOINT", "")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET = os.getenv("R2_BUCKET_NAME", "shortlovers")
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL", "https://stream.shortlovers.id")

R2_READY_DIR = SCRIPT_DIR / "r2_ready" / "melolo"

CONTENT_TYPES = {
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.webp': 'image/webp',
    '.json': 'application/json',
    '.m3u8': 'application/vnd.apple.mpegurl',
    '.ts': 'video/mp2t',
    '.mp4': 'video/mp4',
}


def get_r2_client():
    """Create R2 S3 client"""
    if not all([R2_ENDPOINT, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY]):
        print("❌ R2 credentials missing!")
        print("   Set R2_ENDPOINT, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY in .env")
        sys.exit(1)
    
    return boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name='auto'
    )


def upload_file(s3, local_path: Path, r2_key: str) -> bool:
    """Upload single file to R2"""
    content_type = CONTENT_TYPES.get(local_path.suffix.lower(), 'application/octet-stream')
    try:
        s3.upload_file(
            str(local_path),
            R2_BUCKET,
            r2_key,
            ExtraArgs={'ContentType': content_type}
        )
        return True
    except Exception as e:
        print(f"      ✗ Upload error: {e}")
        return False


def get_uploaded_dramas(s3) -> set:
    """Check which dramas already have data in R2"""
    uploaded = set()
    try:
        paginator = s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=R2_BUCKET, Prefix='melolo/', Delimiter='/'):
            for prefix in page.get('CommonPrefixes', []):
                slug = prefix['Prefix'].replace('melolo/', '').rstrip('/')
                if slug:
                    uploaded.add(slug)
    except Exception as e:
        print(f"  ⚠ Could not list R2 contents: {e}")
    return uploaded


def upload_drama(s3, drama_dir: Path, force=False) -> dict:
    """Upload a complete drama folder to R2"""
    slug = drama_dir.name
    r2_prefix = f"melolo/{slug}"
    
    result = {
        'slug': slug,
        'files_uploaded': 0,
        'files_skipped': 0,
        'bytes_uploaded': 0,
        'errors': [],
    }

    # Upload all files recursively
    all_files = sorted(f for f in drama_dir.rglob('*') if f.is_file())
    
    for fpath in all_files:
        rel = fpath.relative_to(drama_dir)
        r2_key = f"{r2_prefix}/{rel.as_posix()}"
        
        file_size = fpath.stat().st_size
        if file_size == 0:
            continue
        
        if upload_file(s3, fpath, r2_key):
            result['files_uploaded'] += 1
            result['bytes_uploaded'] += file_size
        else:
            result['errors'].append(str(rel))

    return result


def upload_all_dramas(specific_drama=None, force=False):
    """Upload all melolo dramas to R2"""
    print(f"\n{'='*60}")
    print(f"  MELOLO → R2 UPLOADER")
    print(f"{'='*60}\n")

    if not R2_READY_DIR.exists():
        print(f"  ❌ No r2_ready/melolo directory found!")
        return

    # Connect R2
    print("  Connecting to R2...")
    s3 = get_r2_client()
    try:
        s3.head_bucket(Bucket=R2_BUCKET)
        print(f"  ✅ Connected to bucket: {R2_BUCKET}")
    except Exception as e:
        print(f"  ❌ Bucket access failed: {e}")
        return

    # Check existing uploads  
    print("  Checking existing uploads...")
    already_uploaded = get_uploaded_dramas(s3) if not force else set()
    print(f"  Already on R2: {len(already_uploaded)} dramas")

    # Find dramas to upload
    drama_dirs = sorted([d for d in R2_READY_DIR.iterdir() if d.is_dir()])
    
    if specific_drama:
        drama_dirs = [d for d in drama_dirs if d.name == specific_drama]
        if not drama_dirs:
            print(f"  ❌ Drama '{specific_drama}' not found in r2_ready/melolo/")
            return

    # Filter out already uploaded (unless force)
    to_upload = []
    for d in drama_dirs:
        meta_file = d / 'metadata.json'
        has_episodes = any(d.glob('ep*/playlist.m3u8'))
        
        if d.name in already_uploaded and not force:
            continue
        if not has_episodes and not meta_file.exists():
            continue  # Skip empty dirs
        to_upload.append(d)

    print(f"  Dramas to upload: {len(to_upload)}")
    print(f"  Skipped (already on R2): {len(drama_dirs) - len(to_upload)}")

    if not to_upload:
        print(f"\n  ✅ All dramas already uploaded!")
        return

    # Upload each drama
    total_files = 0
    total_bytes = 0
    uploaded_count = 0
    
    print(f"\n{'='*60}")
    print(f"  UPLOADING {len(to_upload)} DRAMAS")
    print(f"{'='*60}")
    
    for i, drama_dir in enumerate(to_upload, 1):
        # Count files
        file_count = sum(1 for f in drama_dir.rglob('*') if f.is_file() and f.stat().st_size > 0)
        
        # Read title from metadata
        title = drama_dir.name
        meta_file = drama_dir / 'metadata.json'
        if meta_file.exists():
            try:
                meta = json.load(open(meta_file, 'r', encoding='utf-8'))
                title = meta.get('title', title)
            except:
                pass
        
        ep_count = sum(1 for _ in drama_dir.glob('ep*/playlist.m3u8'))
        
        print(f"\n  [{i}/{len(to_upload)}] {title} ({ep_count} eps, {file_count} files)")
        
        result = upload_drama(s3, drama_dir, force)
        
        if result['files_uploaded'] > 0:
            size_mb = result['bytes_uploaded'] / (1024 * 1024)
            print(f"    ✅ {result['files_uploaded']} files ({size_mb:.1f} MB)")
            total_files += result['files_uploaded']
            total_bytes += result['bytes_uploaded']
            uploaded_count += 1
        
        if result['errors']:
            print(f"    ⚠ {len(result['errors'])} errors")

    # Update metadata with R2 URLs
    r2_manifest = {
        'source': 'melolo',
        'bucket': R2_BUCKET,
        'public_url': R2_PUBLIC_URL,
        'uploaded_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
        'dramas_uploaded': uploaded_count,
        'total_files': total_files,
        'total_bytes': total_bytes,
    }
    
    manifest_path = SCRIPT_DIR / 'melolo_r2_manifest.json'
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(r2_manifest, f, indent=2, ensure_ascii=False)

    # Summary
    total_mb = total_bytes / (1024 * 1024)
    print(f"\n{'='*60}")
    print(f"  ✅ R2 UPLOAD COMPLETE!")
    print(f"{'='*60}")
    print(f"  Dramas uploaded: {uploaded_count}")  
    print(f"  Files uploaded:  {total_files}")
    print(f"  Total size:      {total_mb:.1f} MB")
    print(f"  Bucket:          {R2_BUCKET}")
    print(f"  Public URL:      {R2_PUBLIC_URL}/melolo/{{slug}}/")
    print(f"  Manifest:        {manifest_path}")


def list_dramas():
    """List all dramas available for upload"""
    if not R2_READY_DIR.exists():
        print("No r2_ready/melolo directory found!")
        return

    dramas = sorted(d for d in R2_READY_DIR.iterdir() if d.is_dir())
    print(f"\nMelolo dramas in r2_ready ({len(dramas)} total):\n")
    
    for i, d in enumerate(dramas, 1):
        ep_count = sum(1 for _ in d.glob('ep*/playlist.m3u8'))
        has_cover = (d / 'cover.jpg').exists()
        has_meta = (d / 'metadata.json').exists()
        
        title = d.name
        if has_meta:
            try:
                meta = json.load(open(d / 'metadata.json', 'r', encoding='utf-8'))
                title = meta.get('title', title)
            except:
                pass
        
        status = f"📺{ep_count:3d}ep"
        if has_cover: status += " 📷"
        if has_meta: status += " 📋"
        
        print(f"  {i:3d}. {status} | {title}")


if __name__ == '__main__':
    if '--list' in sys.argv:
        list_dramas()
    elif '--drama' in sys.argv:
        idx = sys.argv.index('--drama')
        if idx + 1 < len(sys.argv):
            upload_all_dramas(specific_drama=sys.argv[idx + 1])
    else:
        force = '--force' in sys.argv
        upload_all_dramas(force=force)
