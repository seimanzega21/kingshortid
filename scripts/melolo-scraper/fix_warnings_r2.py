#!/usr/bin/env python3
"""
Fix WARNING issues from R2 validation:
1. Upload missing covers
2. Upload missing episodes
3. Fix missing HLS playlists
"""
import boto3, os, json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client('s3',
    endpoint_url=os.getenv('R2_ENDPOINT'),
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
    region_name='auto'
)

BUCKET = 'shortlovers'
LOCAL_DIR = Path('r2_ready/melolo')

CONTENT_TYPES = {
    '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp',
    '.json': 'application/json', '.m3u8': 'application/vnd.apple.mpegurl',
    '.ts': 'video/mp2t', '.mp4': 'video/mp4',
}

print("=" * 80)
print("  FIX R2 WARNING ISSUES")
print("=" * 80)

# Load validation report
with open('r2_validation_report.json', 'r', encoding='utf-8') as f:
    report = json.load(f)

warning_dramas = [d for d in report['dramas'] if d['status'] == 'WARNING']

print(f"\nFound {len(warning_dramas)} dramas with warnings\n")

# 1. Fix missing covers
print("-" * 80)
print("  STEP 1: UPLOADING MISSING COVERS")
print("-" * 80)

cover_fixed = 0
for drama in warning_dramas:
    if 'Missing cover' in str(drama['issues']):
        slug = drama['slug']
        local_cover = None
        
        # Find local cover
        drama_dir = LOCAL_DIR / slug
        for ext in ['.jpg', '.jpeg', '.png', '.webp']:
            cover_path = drama_dir / f'cover{ext}'
            if cover_path.exists() and cover_path.stat().st_size > 100:
                local_cover = cover_path
                break
        
        if not local_cover:
            print(f"⚠️  {slug}: No cover found locally")
            continue
        
        # Upload to R2
        r2_key = f"melolo/{slug}/cover{local_cover.suffix}"
        ct = CONTENT_TYPES.get(local_cover.suffix.lower(), 'image/jpeg')
        
        try:
            s3.upload_file(
                str(local_cover),
                BUCKET,
                r2_key,
                ExtraArgs={'ContentType': ct}
            )
            size_kb = local_cover.stat().st_size // 1024
            print(f"✅ {slug}: Cover uploaded ({size_kb}KB)")
            cover_fixed += 1
        except Exception as e:
            print(f"❌ {slug}: Upload failed - {e}")

print(f"\n  Covers fixed: {cover_fixed}")

# 2. Fix partial episodes
print("\n" + "-" * 80)
print("  STEP 2: UPLOADING MISSING EPISODES")
print("-" * 80)

episode_fixed = 0
for drama in warning_dramas:
    if 'Missing' in str(drama['issues']) and 'episodes' in str(drama['issues']):
        slug = drama['slug']
        drama_dir = LOCAL_DIR / slug / 'episodes'
        
        if not drama_dir.exists():
            print(f"⚠️  {slug}: Episodes directory not found locally")
            continue
        
        # Get local episodes
        local_eps = set()
        for ep_dir in drama_dir.iterdir():
            if ep_dir.is_dir() and (ep_dir / 'playlist.m3u8').exists():
                try:
                    local_eps.add(int(ep_dir.name))
                except:
                    pass
        
        # Get R2 episodes
        r2_eps = set()
        prefix = f"melolo/{slug}/episodes/"
        paginator = s3.get_paginator('list_objects_v2')
        try:
            for page in paginator.paginate(Bucket=BUCKET, Prefix=prefix):
                for obj in page.get('Contents', []):
                    parts = obj['Key'].split('/')
                    if len(parts) >= 4 and parts[3].isdigit():
                        r2_eps.add(int(parts[3]))
        except:
            pass
        
        missing_eps = sorted(local_eps - r2_eps)
        
        if not missing_eps:
            print(f"⚠️  {slug}: No missing episodes found")
            continue
        
        print(f"\n📤 {slug}: Uploading {len(missing_eps)} episodes...")
        
        uploaded = 0
        for ep_num in missing_eps:
            ep_dir = drama_dir / f"{ep_num:03d}"
            if not ep_dir.exists():
                continue
            
            # Upload all files in episode directory
            for file_path in ep_dir.rglob('*'):
                if not file_path.is_file():
                    continue
                
                rel_path = file_path.relative_to(LOCAL_DIR / slug)
                r2_key = f"melolo/{slug}/{rel_path.as_posix()}"
                ct = CONTENT_TYPES.get(file_path.suffix.lower(), 'application/octet-stream')
                
                try:
                    s3.upload_file(
                        str(file_path),
                        BUCKET,
                        r2_key,
                        ExtraArgs={'ContentType': ct}
                    )
                except Exception as e:
                    print(f"  ❌ Ep {ep_num}: {file_path.name} failed")
                    break
            else:
                uploaded += 1
                print(f"  ✅ Ep {ep_num:03d} uploaded")
        
        print(f"  Total: {uploaded}/{len(missing_eps)} episodes uploaded")
        episode_fixed += uploaded

print(f"\n  Episodes fixed: {episode_fixed}")

# 3. Fix missing playlists
print("\n" + "-" * 80)
print("  STEP 3: FIXING MISSING PLAYLISTS")
print("-" * 80)

playlist_fixed = 0
for drama in warning_dramas:
    issues_str = str(drama['issues'])
    if 'no playlist.m3u8' in issues_str:
        slug = drama['slug']
        drama_dir = LOCAL_DIR / slug / 'episodes'
        
        if not drama_dir.exists():
            print(f"⚠️  {slug}: Episodes directory not found locally")
            continue
        
        # Extract episode numbers from issues
        import re
        ep_nums = re.findall(r'Ep (\d+)', issues_str)
        
        print(f"\n📤 {slug}: Uploading playlists for episodes {', '.join(ep_nums)}...")
        
        for ep_str in ep_nums:
            ep_num = int(ep_str)
            ep_dir = drama_dir / f"{ep_num:03d}"
            
            if not ep_dir.exists():
                print(f"  ⚠️  Ep {ep_num:03d}: Not found locally")
                continue
            
            # Upload all files in episode directory
            upload_ok = True
            for file_path in ep_dir.rglob('*'):
                if not file_path.is_file():
                    continue
                
                rel_path = file_path.relative_to(LOCAL_DIR / slug)
                r2_key = f"melolo/{slug}/{rel_path.as_posix()}"
                ct = CONTENT_TYPES.get(file_path.suffix.lower(), 'application/octet-stream')
                
                try:
                    s3.upload_file(
                        str(file_path),
                        BUCKET,
                        r2_key,
                        ExtraArgs={'ContentType': ct}
                    )
                except Exception as e:
                    print(f"  ❌ Ep {ep_num:03d}: Upload failed - {e}")
                    upload_ok = False
                    break
            
            if upload_ok:
                print(f"  ✅ Ep {ep_num:03d}: Playlist uploaded")
                playlist_fixed += 1

print(f"\n  Playlists fixed: {playlist_fixed}")

# Summary
print("\n" + "=" * 80)
print("  FIX COMPLETE")
print("=" * 80)
print(f"  Covers uploaded:    {cover_fixed}")
print(f"  Episodes uploaded:  {episode_fixed}")
print(f"  Playlists fixed:    {playlist_fixed}")
print("=" * 80 + "\n")
