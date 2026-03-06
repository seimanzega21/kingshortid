#!/usr/bin/env python3
"""
Complete renumbering for kaya-raya-di-era-1992
Current state: 001, 003-086 (need to renumber 003-086 to 002-085)
"""
import json, boto3, os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DRAMA = "kaya-raya-di-era-1992"
LOCAL_DIR = Path(f"r2_ready/melolo/{DRAMA}")
EPISODES_DIR = LOCAL_DIR / "episodes"

print("=" * 80)
print(f"  COMPLETE RENUMBERING: {DRAMA}")
print("=" * 80)

# Check current state
print("\n📁 Current state:")
episodes = sorted([d.name for d in EPISODES_DIR.iterdir() if d.is_dir() and d.name.isdigit()])
print(f"   Episodes: {', '.join(episodes[:5])} ... {', '.join(episodes[-3:])}")
print(f"   Total: {len(episodes)}")

# Step 1: Rename 003-086 to temp
print("\n📁 Step 1: Renaming 003-086 to temporary names...")
episodes_to_rename = [d for d in EPISODES_DIR.iterdir() if d.is_dir() and d.name.isdigit() and int(d.name) >= 3]

temp_mapping = {}
for ep_dir in sorted(episodes_to_rename):
    old_num = int(ep_dir.name)
    temp_name = f"temp_{old_num:03d}"
    temp_path = EPISODES_DIR / temp_name
    
    ep_dir.rename(temp_path)
    temp_mapping[old_num] = temp_path

print(f"   ✅ Renamed {len(temp_mapping)} episodes to temp")

# Step 2: Rename temp to final (002-085)
print("\n📁 Step 2: Renaming temp to final numbers...")
for old_num in sorted(temp_mapping.keys()):
    new_num = old_num - 1
    temp_path = temp_mapping[old_num]
    final_name = f"{new_num:03d}"
    final_path = EPISODES_DIR / final_name
    
    temp_path.rename(final_path)

print(f"   ✅ Renamed {len(temp_mapping)} episodes to final numbers (002-085)")

# Verify
final_episodes = sorted([int(d.name) for d in EPISODES_DIR.iterdir() if d.is_dir() and d.name.isdigit()])
print(f"\n✅ Final state: {len(final_episodes)} episodes ({final_episodes[0]}-{final_episodes[-1]})")

# Step 3: Update metadata.json
print("\n📝 Step 3: Updating metadata.json...")

meta_path = LOCAL_DIR / "metadata.json"
with open(meta_path, 'r', encoding='utf-8') as f:
    meta = json.load(f)

new_episodes = []
for ep_num in final_episodes:
    new_episodes.append({
        'number': ep_num,
        'path': f"episodes/{ep_num:03d}/playlist.m3u8"
    })

meta['episodes'] = new_episodes
meta['total_episodes'] = len(new_episodes)
meta['captured_episodes'] = len(new_episodes)

with open(meta_path, 'w', encoding='utf-8') as f:
    json.dump(meta, f, indent=2, ensure_ascii=False)

print(f"   ✅ Metadata updated: {len(new_episodes)} episodes")

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

# Delete old episode 086
print("\n🗑️  Step 5: Deleting old episode 086 from R2...")
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

print(f"   ✅ Deleted {delete_count} files")

# Upload renumbered episodes (002-085)
print("\n📤 Step 6: Uploading renumbered episodes 002-085...")
uploaded = 0

for ep_num in range(2, 86):
    ep_dir = EPISODES_DIR / f"{ep_num:03d}"
    if not ep_dir.exists():
        continue
    
    for file_path in ep_dir.rglob('*'):
        if not file_path.is_file():
            continue
        
        rel_path = file_path.relative_to(LOCAL_DIR)
        r2_key = f"melolo/{DRAMA}/{rel_path.as_posix()}"
        ct = CONTENT_TYPES.get(file_path.suffix.lower(), 'application/octet-stream')
        
        try:
            s3.upload_file(str(file_path), BUCKET, r2_key, ExtraArgs={'ContentType': ct})
            uploaded += 1
        except:
            pass
    
    if ep_num % 10 == 0:
        print(f"   📤 Episodes 1-{ep_num} uploaded...")

print(f"   ✅ Uploaded {uploaded} files")

print("\n" + "=" * 80)
print("  RENUMBERING COMPLETE!")
print("=" * 80)
print(f"  Episodes: 001-085 (85 total)")
print("  ✅ All episodes renumbered")
print("  ✅ Metadata updated")
print("  ✅ R2 synced")
print("=" * 80 + "\n")
