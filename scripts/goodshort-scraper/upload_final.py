#!/usr/bin/env python3
"""
R2 UPLOAD - Correct Bucket
===========================
"""

import boto3
from pathlib import Path

# Paths
SCRIPT_DIR = Path(__file__).parent
CAPTURED_DIR = SCRIPT_DIR / "captured_complete"
COMPLETE_DIR = SCRIPT_DIR / "complete_dramas"

# R2 Config (from user)
R2_ENDPOINT = "https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com"
R2_ACCESS_KEY = "0e4c9b2e8575f0768b06a379f66235a8"
R2_SECRET_KEY = "408927176624f9c5c747f68e0223852e62fb69664ab18a905d0c81e08b9dc903"
R2_BUCKET = "kingshort"
R2_PUBLIC_URL = "https://pub-a9f77e6b702e45b2aabc637183ac0c4d.r2.dev"

print("\n" + "="*70)
print("R2 UPLOAD - KingShort Bucket")
print("="*70)
print(f"Bucket: {R2_BUCKET}")
print(f"Public URL: {R2_PUBLIC_URL}")
print()

# Create S3 client
s3 = boto3.client(
    's3',
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY,
    region_name='auto'
)

print("✅ Connected to R2!")

def upload_file(local_path: Path, r2_key: str):
    """Upload file"""
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
print("UPLOADING")
print("="*70)
print()

uploaded = 0
total_size = 0
drama_slug = "jenderal_jadi_tukang"

# Metadata
print("📋 Metadata...")
for filename in ["metadata.json", "episodes.json", "cover.jpg"]:
    local_file = COMPLETE_DIR / "Jenderal Jadi Tukang" / filename
    if local_file.exists():
        r2_key = f"goodshort/{drama_slug}/{filename}"
        print(f"  {filename}...", end=' ')
        if upload_file(local_file, r2_key):
            print("✅")
            uploaded += 1

# Episodes
print("\n📹 Episodes...")

for episode_folder in sorted(CAPTURED_DIR.glob("episode_*")):
    episode_id = episode_folder.name.replace("episode_", "")
    
    print(f"\n  Episode {episode_id}:")
    
    # Playlist
    segments = sorted(episode_folder.glob("segment_*.ts"))
    playlist_file = episode_folder / "playlist.m3u8"
    
    with open(playlist_file, 'w') as f:
        f.write("#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-TARGETDURATION:10\n#EXT-X-MEDIA-SEQUENCE:0\n")
        for seg in segments:
            f.write(f"#EXTINF:10.0,\n{seg.name}\n")
        f.write("#EXT-X-ENDLIST\n")
    
    # Upload playlist
    r2_key = f"goodshort/{drama_slug}/episode_{episode_id}/playlist.m3u8"
    upload_file(playlist_file, r2_key)
    uploaded += 1
    
    # Upload cover
    cover_file = COMPLETE_DIR / "Jenderal Jadi Tukang" / "cover.jpg"
    if cover_file.exists():
        r2_key = f"goodshort/{drama_slug}/episode_{episode_id}/cover.jpg"
        upload_file(cover_file, r2_key)
        uploaded += 1
    
    # Upload segments
    print(f"    Uploading {len(segments)} segments...", end=' ')
    
    for seg_file in segments:
        r2_key = f"goodshort/{drama_slug}/episode_{episode_id}/{seg_file.name}"
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
print("📍 PUBLIC URLS:")
print(f"\n🎬 Drama Cover:")
print(f"  {R2_PUBLIC_URL}/goodshort/{drama_slug}/cover.jpg")
print()
print("📺 Episodes:")

for episode_folder in sorted(CAPTURED_DIR.glob("episode_*")):
    episode_id = episode_folder.name.replace("episode_", "")
    print(f"  Episode {episode_id}: {R2_PUBLIC_URL}/goodshort/{drama_slug}/episode_{episode_id}/playlist.m3u8")

print()
print("✅ Ready for mobile app!")
print()
