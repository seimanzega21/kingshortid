#!/usr/bin/env python3
"""
Renumber episodes for kaya-raya-di-era-1992
From: 002-086 (85 episodes)
To:   001-085 (85 episodes)

Strategy: Use temp names to avoid conflicts
"""
import json, shutil, boto3, os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DRAMA = "kaya-raya-di-era-1992"
LOCAL_DIR = Path(f"r2_ready/melolo/{DRAMA}")
EPISODES_DIR = LOCAL_DIR / "episodes"

print("=" * 80)
print(f"  RENUMBER EPISODES: {DRAMA}")
print("=" * 80)

# Step 1: Rename to temp names first
print("\n📁 Step 1: Renaming to temporary names...")

episodes = sorted([d for d in EPISODES_DIR.iterdir() if d.is_dir() and d.name.isdigit()])
print(f"   Found {len(episodes)} episodes")

temp_mapping = {}
for ep_dir in episodes:
    old_num = int(ep_dir.name)
    temp_name = f"temp_{old_num:03d}"
    temp_path = EPISODES_DIR / temp_name
    
    ep_dir.rename(temp_path)
    temp_mapping[old_num] = temp_path
    print(f"   ✅ {ep_dir.name} → {temp_name}")

print(f"\n   Total: {len(temp_mapping)} renamed to temp")

# Step 2: Rename from temp to final numbers
print("\n📁 Step 2: Renaming to final numbers...")

final_mapping = {}
for old_num in sorted(temp_mapping.keys()):
    new_num = old_num - 1
    
    if new_num < 1:
        print(f"   ⚠️  Skipping temp_{old_num:03d} (would become 000)")
        continue
    
    temp_path = temp_mapping[old_num]
    final_name = f"{new_num:03d}"
    final_path = EPISODES_DIR / final_name
    
    temp_path.rename(final_path)
    final_mapping[new_num] = final_path
    print(f"   ✅ temp_{old_num:03d} → {final_name}")

print(f"\n   Total: {len(final_mapping)} episodes (001-{max(final_mapping.keys()):03d})")

# Step 3: Update metadata.json
print("\n📝 Step 3: Updating metadata.json...")

meta_path = LOCAL_DIR / "metadata.json"
with open(meta_path, 'r', encoding='utf-8') as f:
    meta = json.load(f)

# Create new episode list
new_episodes = []
for ep_num in sorted(final_mapping.keys()):
    new_episodes.append({
        'number': ep_num,
        'path': f"episodes/{ep_num:03d}/playlist.m3u8"
    })

meta['episodes'] = new_episodes
meta['total_episodes'] = len(new_episodes)
meta['captured_episodes'] = len(new_episodes)

with open(meta_path, 'w', encoding='utf-8') as f:
    json.dump(meta, f, indent=2, ensure_ascii=False)

print(f"   ✅ Metadata updated: {len(new_episodes)} episodes (1-{len(new_episodes)})")

# Step 4: Upload to R2
print("\n📤 Step 4: Uploading to R2...")

s3 = boto3.client('s3',
    endpoint_url=os.getenv('R2_ENDPOINT'),
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
    region_name='auto'
)

BUCKET = 'shortlovers'
CONTENT_TYPES = {
    '.jpg': 'image/jpeg', '.json': 'application/json',
    '.m3u8': 'application/vnd.apple.mpegurl', '.ts': 'video/mp2t',
}

# Upload metadata
r2_key = f"melolo/{DRAMA}/metadata.json"
s3.upload_file(str(meta_path), BUCKET, r2_key, ExtraArgs={'ContentType': 'application/json'})
print(f"   ✅ Metadata uploaded")

# Delete old episode 086 from R2
print("\n🗑️  Step 5: Cleaning up old episode 086 from R2...")
prefix = f"melolo/{DRAMA}/episodes/086/"
delete_count = 0

try:
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=BUCKET, Prefix=prefix):
        for obj in page.get('Contents', []):
            s3.delete_object(Bucket=BUCKET, Key=obj['Key'])
            delete_count += 1
except:
    pass

print(f"   ✅ Deleted {delete_count} files from episode 086")

# Upload all renumbered episodes
print("\n📤 Step 6: Uploading renumbered episodes...")
uploaded = 0
uploaded_eps = []

for ep_num in sorted(final_mapping.keys()):
    ep_dir = final_mapping[ep_num]
    
    # Upload all files in episode
    for file_path in ep_dir.rglob('*'):
        if not file_path.is_file():
            continue
        
        rel_path = file_path.relative_to(LOCAL_DIR)
        r2_key = f"melolo/{DRAMA}/{rel_path.as_posix()}"
        ct = CONTENT_TYPES.get(file_path.suffix.lower(), 'application/octet-stream')
        
        try:
            s3.upload_file(str(file_path), BUCKET, r2_key, ExtraArgs={'ContentType': ct})
            uploaded += 1
        except Exception as e:
            print(f"   ❌ Failed: {r2_key}")
    
    uploaded_eps.append(ep_num)
    if ep_num % 10 == 0:
        print(f"   📤 Uploaded episodes 1-{ep_num}...")

print(f"   ✅ Uploaded {uploaded} files for {len(uploaded_eps)} episodes")

print("\n" + "=" * 80)
print("  RENUMBERING COMPLETE!")
print("=" * 80)
print(f"  Episodes now: 001-{max(final_mapping.keys()):03d} ({len(final_mapping)} total)")
print("  ✅ Local folders renumbered")
print("  ✅ Metadata updated")
print("  ✅ R2 updated")
print("=" * 80 + "\n")
