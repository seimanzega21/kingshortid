#!/usr/bin/env python3
"""
Upload r2_ready folder to Cloudflare R2 - KINGSHORT BUCKET
Uploads MP4 episodes, covers, and metadata to the "kingshort" bucket
"""

import boto3
import os
import json
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
R2_READY_DIR = SCRIPT_DIR / "r2_ready"

# R2 Config - Read from environment or use defaults
R2_ENDPOINT = os.environ.get("R2_ENDPOINT")
R2_ACCESS_KEY_ID = os.environ.get("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.environ.get("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = "kingshort"  # Fixed bucket name as requested
R2_PUBLIC_URL = "https://stream.shortlovers.id"  # Default public URL

print("\n" + "="*70)
print("R2 UPLOAD - KINGSHORT BUCKET")
print("="*70)
print()

# Check if credentials are provided
if not R2_ENDPOINT or not R2_ACCESS_KEY_ID or not R2_SECRET_ACCESS_KEY:
    print("⚠️  R2 credentials not found in environment variables")
    print()
    print("Please provide R2 credentials:")
    print()
    
    if not R2_ENDPOINT:
        print("Example: https://abc123.r2.cloudflarestorage.com")
        R2_ENDPOINT = input("R2_ENDPOINT: ").strip()
    
    if not R2_ACCESS_KEY_ID:
        R2_ACCESS_KEY_ID = input("R2_ACCESS_KEY_ID: ").strip()
    
    if not R2_SECRET_ACCESS_KEY:
        R2_SECRET_ACCESS_KEY = input("R2_SECRET_ACCESS_KEY: ").strip()
    
    print()

# Display config
print("Configuration:")
print(f"  Endpoint: {R2_ENDPOINT}")
print(f"  Bucket: {R2_BUCKET_NAME}")
print(f"  Public URL: {R2_PUBLIC_URL}")
print()

# Validate
if not all([R2_ENDPOINT, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY]):
    print("❌ Missing required credentials!")
    exit(1)

# Create S3 client
try:
    s3 = boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name='auto'
    )
    
    # Test connection
    s3.list_buckets()
    print("✅ R2 client connected successfully!")
    print()
    
except Exception as e:
    print(f"❌ Failed to connect to R2: {e}")
    exit(1)

def upload_file(local_path: Path, r2_key: str):
    """Upload single file to R2"""
    
    # Content type
    content_type = 'application/octet-stream'
    if local_path.suffix == '.mp4':
        content_type = 'video/mp4'
    elif local_path.suffix in ['.jpg', '.jpeg']:
        content_type = 'image/jpeg'
    elif local_path.suffix == '.json':
        content_type = 'application/json'
    
    try:
        file_size = local_path.stat().st_size
        
        # For large files, use multipart upload
        if file_size > 100 * 1024 * 1024:  # > 100MB
            print(f"      (Large file, using multipart upload)")
        
        s3.upload_file(
            str(local_path),
            R2_BUCKET_NAME,
            r2_key,
            ExtraArgs={
                'ContentType': content_type
            }
        )
        return True
    except Exception as e:
        print(f"      ❌ Error: {str(e)[:100]}")
        return False

# Load manifest
manifest_file = R2_READY_DIR / "r2_manifest.json"
if not manifest_file.exists():
    print(f"❌ Manifest not found: {manifest_file}")
    exit(1)

with open(manifest_file, 'r', encoding='utf-8') as f:
    manifest = json.load(f)

print("="*70)
print("UPLOADING TO R2")
print("="*70)
print(f"\nDramas: {manifest['total_dramas']}")
print(f"Episodes: {manifest['total_episodes']}")
print(f"Total Size: {manifest['total_size_mb']:.1f} MB")
print()

uploaded = 0
failed = 0
total_size_mb = 0
upload_details = []

# Upload each drama
for drama in manifest['dramas']:
    drama_slug = drama['folder']
    drama_folder = R2_READY_DIR / drama_slug
    
    print(f"{'='*70}")
    print(f"📁 {drama['title']}")
    print(f"{'='*70}")
    
    drama_upload = {
        'title': drama['title'],
        'slug': drama_slug,
        'cover_url': None,
        'metadata_url': None,
        'episodes': []
    }
    
    # Upload cover
    cover_file = drama_folder / "cover.jpg"
    if cover_file.exists():
        r2_key = f"goodshort/{drama_slug}/cover.jpg"
        print(f"  📷 Uploading cover... ", end='', flush=True)
        if upload_file(cover_file, r2_key):
            print("✅")
            uploaded += 1
            file_size_mb = cover_file.stat().st_size / (1024 * 1024)
            total_size_mb += file_size_mb
            drama_upload['cover_url'] = f"{R2_PUBLIC_URL}/{r2_key}"
        else:
            print("❌")
            failed += 1
    
    # Upload metadata
    metadata_file = drama_folder / "metadata.json"
    if metadata_file.exists():
        r2_key = f"goodshort/{drama_slug}/metadata.json"
        print(f"  📋 Uploading metadata... ", end='', flush=True)
        if upload_file(metadata_file, r2_key):
            print("✅")
            uploaded += 1
            drama_upload['metadata_url'] = f"{R2_PUBLIC_URL}/{r2_key}"
        else:
            print("❌")
            failed += 1
    
    # Upload episodes
    episodes_folder = drama_folder / "episodes"
    episode_files = sorted(episodes_folder.glob("episode_*.mp4"))
    
    print(f"\n  📹 Uploading {len(episode_files)} episodes:")
    
    for ep_file in episode_files:
        episode_num = ep_file.stem.replace('episode_', '')
        r2_key = f"goodshort/{drama_slug}/episodes/{ep_file.name}"
        
        file_size_mb = ep_file.stat().st_size / (1024 * 1024)
        print(f"    Episode {episode_num} ({file_size_mb:.1f} MB)... ", end='', flush=True)
        
        if upload_file(ep_file, r2_key):
            print("✅")
            uploaded += 1
            total_size_mb += file_size_mb
            
            drama_upload['episodes'].append({
                'number': int(episode_num),
                'filename': ep_file.name,
                'url': f"{R2_PUBLIC_URL}/{r2_key}",
                'size_mb': file_size_mb
            })
        else:
            print("❌")
            failed += 1
    
    upload_details.append(drama_upload)
    print()

# Save upload report
report = {
    'bucket': R2_BUCKET_NAME,
    'public_url': R2_PUBLIC_URL,
    'uploaded_files': uploaded,
    'failed_files': failed,
    'total_size_mb': total_size_mb,
    'dramas': upload_details
}

report_file = SCRIPT_DIR / "r2_upload_report.json"
with open(report_file, 'w', encoding='utf-8') as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

# Summary
print("="*70)
print("UPLOAD COMPLETE!")
print("="*70)
print(f"\n📊 Statistics:")
print(f"  ✅ Uploaded: {uploaded} files")
print(f"  ❌ Failed: {failed} files")
print(f"  📦 Total Size: {total_size_mb:.1f} MB")
print(f"  🪣 Bucket: {R2_BUCKET_NAME}")

print(f"\n📍 PUBLIC URLS:")
for drama in upload_details:
    print(f"\n{drama['title']}:")
    if drama['cover_url']:
        print(f"  Cover: {drama['cover_url']}")
    if drama['metadata_url']:
        print(f"  Metadata: {drama['metadata_url']}")
    if drama['episodes']:
        print(f"  Episodes: {len(drama['episodes'])} videos")
        for ep in drama['episodes'][:3]:  # Show first 3
            print(f"    Ep {ep['number']}: {ep['url']}")
        if len(drama['episodes']) > 3:
            print(f"    ... and {len(drama['episodes']) - 3} more")

print(f"\n📄 Upload report saved to: {report_file}")
print("\n✅ Upload complete! Ready for database import!")
print()
