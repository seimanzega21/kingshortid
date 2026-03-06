#!/usr/bin/env python3
"""
DIRECT R2 UPLOAD - Upload Captured Videos
==========================================

Upload captured episodes directly to R2 storage.
"""

import boto3
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Paths
SCRIPT_DIR = Path(__file__).parent
CAPTURED_DIR = SCRIPT_DIR / "captured_complete"
COMPLETE_DIR = SCRIPT_DIR / "complete_dramas"

# R2 Config from .env
R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "shortlovers")
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL", "https://stream.shortlovers.id")

# Extract account ID from endpoint
if R2_ENDPOINT:
    import re
    match = re.search(r'https://(\w+)\.r2\.cloudflarestorage\.com', R2_ENDPOINT)
    R2_ACCOUNT_ID = match.group(1) if match else None
else:
    R2_ACCOUNT_ID = None

print("\n" + "="*70)
print("R2 DIRECT UPLOAD")
print("="*70)
print()
print("Checking credentials...")
print(f"  Endpoint: {R2_ENDPOINT}")
print(f"  Bucket: {R2_BUCKET_NAME}")
print(f"  Public URL: {R2_PUBLIC_URL}")
print()

# Create S3 client
try:
    s3 = boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name='auto'
    )
    print("✅ R2 client connected!")
except Exception as e:
    print(f"❌ Failed to connect: {e}")
    exit(1)

# Upload function
def upload_file(local_path: Path, r2_key: str):
    """Upload single file"""
    
    # Content type
    content_type = 'application/octet-stream'
    if local_path.suffix == '.ts':
        content_type = 'video/mp2t'
    elif local_path.suffix == '.m3u8':
        content_type = 'application/vnd.apple.mpegurl'
    elif local_path.suffix in ['.jpg', '.jpeg']:
        content_type = 'image/jpeg'
    elif local_path.suffix == '.json':
        content_type = 'application/json'
    
    try:
        s3.upload_file(
            str(local_path),
            R2_BUCKET_NAME,
            r2_key,
            ExtraArgs={
                'ContentType': content_type,
                'ACL': 'public-read'
            }
        )
        return True
    except Exception as e:
        print(f"      ❌ {e}")
        return False

# Main upload
print()
print("="*70)
print("UPLOADING CAPTURED VIDEOS")
print("="*70)
print()

uploaded = 0
failed = 0
total_size = 0

# Drama slug (default to "jenderal_jadi_tukang")
drama_slug = "jenderal_jadi_tukang"

# Upload metadata
print("📋 Uploading metadata...")
metadata_files = [
    (COMPLETE_DIR / "Jenderal Jadi Tukang" / "metadata.json", "metadata.json"),
    (COMPLETE_DIR / "Jenderal Jadi Tukang" / "episodes.json", "episodes.json"),
    (COMPLETE_DIR / "Jenderal Jadi Tukang" / "cover.jpg", "cover.jpg"),
]

for local_file, filename in metadata_files:
    if local_file.exists():
        r2_key = f"goodshort/{drama_slug}/{filename}"
        print(f"  {filename}...", end=' ')
        if upload_file(local_file, r2_key):
            print("✅")
            uploaded += 1
        else:
            print("❌")
            failed += 1

# Upload episodes
print("\n📹 Uploading episodes...")

for episode_folder in CAPTURED_DIR.glob("episode_*"):
    episode_id = episode_folder.name.replace("episode_", "")
    
    print(f"\n  Episode {episode_id}:")
    
    # Create playlist first
    segments = sorted(episode_folder.glob("segment_*.ts"))
    playlist_file = episode_folder / "playlist.m3u8"
    
    with open(playlist_file, 'w') as f:
        f.write("#EXTM3U\n")
        f.write("#EXT-X-VERSION:3\n")
        f.write("#EXT-X-TARGETDURATION:10\n")
        f.write("#EXT-X-MEDIA-SEQUENCE:0\n")
        for seg in segments:
            f.write("#EXTINF:10.0,\n")
            f.write(f"{seg.name}\n")
        f.write("#EXT-X-ENDLIST\n")
    
    # Upload playlist
    r2_key = f"goodshort/{drama_slug}/episode_{episode_id}/playlist.m3u8"
    print(f"    playlist.m3u8...", end=' ')
    if upload_file(playlist_file, r2_key):
        print("✅")
        uploaded += 1
    else:
        print("❌")
        failed += 1
    
    # Upload cover
    cover_file = COMPLETE_DIR / "Jenderal Jadi Tukang" / "cover.jpg"
    if cover_file.exists():
        r2_key = f"goodshort/{drama_slug}/episode_{episode_id}/cover.jpg"
        upload_file(cover_file, r2_key)
    
    # Upload segments
    print(f"    Uploading {len(segments)} segments...")
    for i, seg_file in enumerate(segments):
        r2_key = f"goodshort/{drama_slug}/episode_{episode_id}/{seg_file.name}"
        
        success = upload_file(seg_file, r2_key)
        if success:
            uploaded += 1
            total_size += seg_file.stat().st_size
        else:
            failed += 1
        
        # Progress
        if (i + 1) % 20 == 0:
            print(f"      {i+1}/{len(segments)}...", end='\r')
    
    print(f"    ✅ {len(segments)} segments uploaded")

# Summary
print()
print("="*70)
print("UPLOAD COMPLETE!")
print("="*70)
print(f"Uploaded: {uploaded} files")
print(f"Failed: {failed} files")
print(f"Size: {total_size / 1024 / 1024:.2f} MB")
print()
print("📍 R2 URLS:")
print(f"  Cover: {R2_PUBLIC_URL}/goodshort/{drama_slug}/cover.jpg")

for episode_folder in CAPTURED_DIR.glob("episode_*"):
    episode_id = episode_folder.name.replace("episode_", "")
    print(f"  Episode {episode_id}: {R2_PUBLIC_URL}/goodshort/{drama_slug}/episode_{episode_id}/playlist.m3u8")

print()
print("✅ Ready to test in mobile app!")
print()
