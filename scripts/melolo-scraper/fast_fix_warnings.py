#!/usr/bin/env python3
"""
FAST fix for WARNING R2 issues — uses 10 parallel workers
"""
import boto3, os, json
from pathlib import Path
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

load_dotenv()

s3 = boto3.client('s3',
    endpoint_url=os.getenv('R2_ENDPOINT'),
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
    region_name='auto'
)

BUCKET = 'shortlovers'
LOCAL_DIR = Path('r2_ready/melolo')
WORKERS = 10
lock = threading.Lock()
stats = {'uploaded': 0, 'failed': 0}

CT = {
    '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp',
    '.json': 'application/json', '.m3u8': 'application/vnd.apple.mpegurl',
    '.ts': 'video/mp2t', '.mp4': 'video/mp4',
}

def upload_file(local_path, r2_key):
    ct = CT.get(local_path.suffix.lower(), 'application/octet-stream')
    try:
        s3.upload_file(str(local_path), BUCKET, r2_key, ExtraArgs={'ContentType': ct})
        with lock:
            stats['uploaded'] += 1
        return True
    except:
        with lock:
            stats['failed'] += 1
        return False

def get_r2_episodes(slug):
    """Get set of episode numbers on R2"""
    eps = set()
    prefix = f"melolo/{slug}/episodes/"
    paginator = s3.get_paginator('list_objects_v2')
    try:
        for page in paginator.paginate(Bucket=BUCKET, Prefix=prefix):
            for obj in page.get('Contents', []):
                parts = obj['Key'].split('/')
                if len(parts) >= 4:
                    try: eps.add(int(parts[3]))
                    except: pass
    except: pass
    return eps

def fix_drama_episodes(slug):
    """Find and upload missing episodes for a drama"""
    episodes_dir = LOCAL_DIR / slug / 'episodes'
    if not episodes_dir.exists():
        return 0

    # Get local episodes
    local_eps = set()
    for ep_dir in episodes_dir.iterdir():
        if ep_dir.is_dir() and ep_dir.name.isdigit():
            if (ep_dir / 'playlist.m3u8').exists() or any(ep_dir.glob('*.mp4')):
                local_eps.add(int(ep_dir.name))

    # Get R2 episodes
    r2_eps = get_r2_episodes(slug)
    missing = sorted(local_eps - r2_eps)

    if not missing:
        return 0

    print(f"  📤 {slug}: {len(missing)} missing eps")

    # Collect all files to upload
    upload_tasks = []
    for ep_num in missing:
        ep_dir = episodes_dir / f"{ep_num:03d}"
        if not ep_dir.exists():
            continue
        for file_path in ep_dir.rglob('*'):
            if not file_path.is_file():
                continue
            rel_path = file_path.relative_to(LOCAL_DIR / slug)
            r2_key = f"melolo/{slug}/{rel_path.as_posix()}"
            upload_tasks.append((file_path, r2_key))

    # Upload in parallel
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futures = [ex.submit(upload_file, lp, rk) for lp, rk in upload_tasks]
        for f in as_completed(futures):
            pass

    print(f"  ✅ {slug}: {len(upload_tasks)} files uploaded")
    return len(missing)

def fix_drama_cover(slug):
    """Upload missing cover"""
    drama_dir = LOCAL_DIR / slug
    for ext in ['.jpg', '.jpeg', '.png', '.webp']:
        cover = drama_dir / f'cover{ext}'
        if cover.exists() and cover.stat().st_size > 100:
            r2_key = f"melolo/{slug}/cover{ext}"
            if upload_file(cover, r2_key):
                print(f"  ✅ {slug}: Cover uploaded")
                return True
    
    # Try poster
    for ext in ['.jpg', '.jpeg', '.png', '.webp']:
        poster = drama_dir / f'poster{ext}'
        if poster.exists() and poster.stat().st_size > 100:
            r2_key = f"melolo/{slug}/poster{ext}"
            if upload_file(poster, r2_key):
                print(f"  ✅ {slug}: Poster uploaded")
                return True
    
    print(f"  ⚠️  {slug}: No cover found locally")
    return False

def fix_playlists(slug, issues):
    """Re-upload episodes with missing playlists"""
    import re
    episodes_dir = LOCAL_DIR / slug / 'episodes'
    if not episodes_dir.exists():
        return 0

    ep_nums = re.findall(r'Ep (\d+)', str(issues))
    if not ep_nums:
        return 0

    upload_tasks = []
    for ep_str in ep_nums:
        ep_dir = episodes_dir / f"{int(ep_str):03d}"
        if not ep_dir.exists():
            continue
        for file_path in ep_dir.rglob('*'):
            if not file_path.is_file():
                continue
            rel_path = file_path.relative_to(LOCAL_DIR / slug)
            r2_key = f"melolo/{slug}/{rel_path.as_posix()}"
            upload_tasks.append((file_path, r2_key))

    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futures = [ex.submit(upload_file, lp, rk) for lp, rk in upload_tasks]
        for f in as_completed(futures):
            pass

    print(f"  ✅ {slug}: {len(ep_nums)} playlists fixed ({len(upload_tasks)} files)")
    return len(ep_nums)

# Main
print("=" * 70)
print("  FAST FIX R2 WARNINGS (10 parallel workers)")
print("=" * 70)

with open('r2_validation_report.json', 'r', encoding='utf-8') as f:
    report = json.load(f)

warnings = [d for d in report['dramas'] if d['status'] == 'WARNING']
print(f"\n  {len(warnings)} dramas with warnings\n")

covers_fixed = 0
episodes_fixed = 0
playlists_fixed = 0

for drama in warnings:
    slug = drama['slug']
    issues = drama['issues']
    issues_str = str(issues)

    # Fix missing covers
    if 'Missing cover' in issues_str:
        if fix_drama_cover(slug):
            covers_fixed += 1

    # Fix missing episodes
    if 'Missing' in issues_str and 'episodes' in issues_str:
        episodes_fixed += fix_drama_episodes(slug)

    # Fix missing playlists
    if 'no playlist.m3u8' in issues_str:
        playlists_fixed += fix_playlists(slug, issues)

print("\n" + "=" * 70)
print("  DONE!")
print("=" * 70)
print(f"  Covers fixed:    {covers_fixed}")
print(f"  Episodes fixed:  {episodes_fixed}")
print(f"  Playlists fixed: {playlists_fixed}")
print(f"  Files uploaded:  {stats['uploaded']}")
print(f"  Files failed:    {stats['failed']}")
print("=" * 70)
