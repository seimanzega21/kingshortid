#!/usr/bin/env python3
"""
R2 REORGANIZE - Upload dengan episode numbering yang rapi
==========================================================
"""

import boto3
from pathlib import Path

# Config
SCRIPT_DIR = Path(__file__).parent
CAPTURED_DIR = SCRIPT_DIR / "captured_complete"
COMPLETE_DIR = SCRIPT_DIR / "complete_dramas"

# R2
R2_ENDPOINT = "https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com"
R2_ACCESS_KEY = "0e4c9b2e8575f0768b06a379f66235a8"
R2_SECRET_KEY = "408927176624f9c5c747f68e0223852e62fb69664ab18a905d0c81e08b9dc903"
R2_BUCKET = "kingshort"
R2_PUBLIC_URL = "https://pub-a9f77e6b702e45b2aabc637183ac0c4d.r2.dev"

print("\n" + "="*70)
print("R2 REORGANIZE - Sequential Episode Numbers")
print("="*70)
print()

# Connect
s3 = boto3.client(
    's3',
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY,
    region_name='auto'
)

print("✅ Connected!")

def upload_file(local_path: Path, r2_key: str):
    """Upload file"""
    content_type = {
        '.ts': 'video/mp2t',
        '.m3u8': 'application/vnd.apple.mpegurl',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.json': 'application/json'
    }.get(local_path.suffix, 'application/octet-stream')
    
    try:
        s3.upload_file(
            str(local_path),
            R2_BUCKET,
            r2_key,
            ExtraArgs={
                'ContentType': content_type,
                'ACL': 'public-read'
            }
        )
        return True
    except Exception as e:
        print(f"  ❌ {e}")
        return False

# Upload
print("\n" + "="*70)
print("UPLOADING WITH SEQUENTIAL NUMBERS")
print("="*70)
print()

drama_slug = "jenderal_jadi_tukang"
uploaded = 0
total_size = 0

# Delete old episodes first
print("🗑️  Cleaning old uploads...")
try:
    # List and delete old episode folders
    paginator = s3.get_paginator('list_objects_v2')
    for result in paginator.paginate(Bucket=R2_BUCKET, Prefix=f"goodshort/{drama_slug}/episode_"):
        if 'Contents' in result:
            objects = [{'Key': obj['Key']} for obj in result['Contents']]
            if objects:
                s3.delete_objects(Bucket=R2_BUCKET, Delete={'Objects': objects})
                print(f"  Deleted {len(objects)} old files")
except Exception as e:
    print(f"  ⚠️  {e}")

# Upload metadata
print("\n📋 Uploading metadata...")
for filename in ["metadata.json", "episodes.json", "cover.jpg"]:
    local_file = COMPLETE_DIR / "Jenderal Jadi Tukang" / filename
    if local_file.exists():
        r2_key = f"goodshort/{drama_slug}/{filename}"
        print(f"  {filename}...", end=' ')
        if upload_file(local_file, r2_key):
            print("✅")
            uploaded += 1

# Get episodes and sort
episode_folders = sorted(CAPTURED_DIR.glob("episode_*"))

print(f"\n📹 Uploading {len(episode_folders)} episodes with sequential numbers...")

# Upload episodes with sequential numbering
for ep_num, episode_folder in enumerate(episode_folders, 1):
    original_id = episode_folder.name.replace("episode_", "")
    
    print(f"\n  Episode {ep_num} (original ID: {original_id}):")
    
    # Get segments
    segments = sorted(episode_folder.glob("segment_*.ts"))
    
    if not segments:
        print(f"    ⚠️  No segments found, skipping")
        continue
    
    # Create playlist
    playlist_file = episode_folder / f"playlist_ep{ep_num}.m3u8"
    
    with open(playlist_file, 'w') as f:
        f.write("#EXTM3U\n")
        f.write("#EXT-X-VERSION:3\n")
        f.write("#EXT-X-TARGETDURATION:10\n")
        f.write("#EXT-X-MEDIA-SEQUENCE:0\n")
        for seg in segments:
            f.write("#EXTINF:10.0,\n")
            f.write(f"{seg.name}\n")
        f.write("#EXT-X-ENDLIST\n")
    
    # Upload to ep_1, ep_2, etc.
    ep_folder_name = f"ep_{ep_num}"
    
    # Upload playlist
    r2_key = f"goodshort/{drama_slug}/{ep_folder_name}/playlist.m3u8"
    print(f"    playlist.m3u8...", end=' ')
    upload_file(playlist_file, r2_key)
    uploaded += 1
    print("✅")
    
    # Upload cover
    cover_file = COMPLETE_DIR / "Jenderal Jadi Tukang" / "cover.jpg"
    if cover_file.exists():
        r2_key = f"goodshort/{drama_slug}/{ep_folder_name}/cover.jpg"
        upload_file(cover_file, r2_key)
        uploaded += 1
    
    # Upload segments
    print(f"    Uploading {len(segments)} segments...", end=' ')
    
    for seg_file in segments:
        r2_key = f"goodshort/{drama_slug}/{ep_folder_name}/{seg_file.name}"
        if upload_file(seg_file, r2_key):
            uploaded += 1
            total_size += seg_file.stat().st_size
    
    print(f"✅")

# Summary
print()
print("="*70)
print("COMPLETE!")
print("="*70)
print(f"Uploaded: {uploaded} files")
print(f"Size: {total_size / 1024 / 1024:.2f} MB")
print()
print("📁 R2 STRUCTURE:")
print(f"  goodshort/{drama_slug}/")
print(f"    ├── cover.jpg")
print(f"    ├── metadata.json")
print(f"    ├── episodes.json")
print(f"    ├── ep_1/")
print(f"    │   ├── playlist.m3u8")
print(f"    │   ├── cover.jpg")
print(f"    │   └── segment_*.ts")
print(f"    └── ep_2/")
print(f"        ├── playlist.m3u8")
print(f"        ├── cover.jpg")
print(f"        └── segment_*.ts")
print()
print("📍 PUBLIC URLS:")
print(f"\n🎬 Drama:")
print(f"  {R2_PUBLIC_URL}/goodshort/{drama_slug}/cover.jpg")
print()
print("📺 Episodes:")

for ep_num in range(1, len(episode_folders) + 1):
    print(f"  Episode {ep_num}: {R2_PUBLIC_URL}/goodshort/{drama_slug}/ep_{ep_num}/playlist.m3u8")

print()
print("✅ Tersusun rapi dengan episode 1, 2, 3!")
print()
