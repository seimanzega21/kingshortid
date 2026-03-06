#!/usr/bin/env python3
"""
1. Check if local data for 4 deleted dramas still exists
2. Re-upload them to R2 if local data exists
3. Full R2 audit for ALL active dramas in DB
"""
import os, json, re, boto3, requests
from pathlib import Path
from dotenv import load_dotenv
from botocore.config import Config

load_dotenv(Path(__file__).parent / '.env')

config = Config(retries={'max_attempts': 3}, connect_timeout=10, read_timeout=30)
s3 = boto3.client('s3',
    endpoint_url=os.getenv('R2_ENDPOINT'),
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
    region_name='auto', config=config)
BUCKET = os.getenv('R2_BUCKET_NAME', 'shortlovers')
R2_PUBLIC = 'https://stream.shortlovers.id'
LOCAL_BASE = 'r2_ready/melolo'

# R2 slugs for the 4 deleted dramas
DELETED_SLUGS = [
    'misi-cinta-sang-kurir',          # Metha Delivery King
    'mata-kiri-ajaibku',              # Martial Master Returns
    'kehadiran-cinta-dari-masa-lalu', # Harta Karun Nusantara
    'kekuatan-dewa-pemegang-jus',     # Kekuatan Dewa Pemegang Jus
]

print('='*70)
print('  STEP 1: CHECK LOCAL DATA FOR 4 DELETED DRAMAS')
print('='*70)

for slug in DELETED_SLUGS:
    local_dir = os.path.join(LOCAL_BASE, slug)
    if os.path.isdir(local_dir):
        items = os.listdir(local_dir)
        meta_path = os.path.join(local_dir, 'metadata.json')
        has_meta = os.path.exists(meta_path)
        
        # Count episode dirs
        ep_dirs = [d for d in items if d.startswith('ep') or d.startswith('episodes')]
        
        print(f'\n  ✅ {slug}: LOCAL EXISTS')
        print(f'     Items: {len(items)}, Has metadata: {has_meta}, Episode dirs: {len(ep_dirs)}')
        
        if has_meta:
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            print(f'     Title: {meta.get("title", "?")}')
            print(f'     Total eps: {meta.get("total_episodes", 0)}')
    else:
        print(f'\n  ❌ {slug}: LOCAL NOT FOUND')

# Check what's on R2 for these slugs
print(f'\n{"="*70}')
print('  STEP 2: CHECK R2 STATUS FOR DELETED DRAMAS')
print('='*70)

for slug in DELETED_SLUGS:
    prefix = f'melolo/{slug}/'
    r2_files = []
    continuation = None
    
    while True:
        kwargs = {'Bucket': BUCKET, 'Prefix': prefix, 'MaxKeys': 1000}
        if continuation:
            kwargs['ContinuationToken'] = continuation
        resp = s3.list_objects_v2(**kwargs)
        r2_files.extend(resp.get('Contents', []))
        if not resp.get('IsTruncated'):
            break
        continuation = resp.get('NextContinuationToken')
    
    if r2_files:
        total_size = sum(f['Size'] for f in r2_files)
        print(f'\n  ✅ {slug}: {len(r2_files)} files on R2 ({total_size/1024/1024:.1f} MB)')
    else:
        print(f'\n  ❌ {slug}: EMPTY on R2 - needs re-upload!')
        
        # Re-upload from local
        local_dir = os.path.join(LOCAL_BASE, slug)
        if os.path.isdir(local_dir):
            print(f'     📤 Re-uploading from local...')
            uploaded = 0
            for root, dirs, files in os.walk(local_dir):
                for fname in files:
                    local_path = os.path.join(root, fname)
                    rel = os.path.relpath(local_path, LOCAL_BASE).replace('\\', '/')
                    r2_key = f'melolo/{rel}'
                    
                    # Determine content type
                    ct = 'application/octet-stream'
                    if fname.endswith('.m3u8'): ct = 'application/vnd.apple.mpegurl'
                    elif fname.endswith('.ts'): ct = 'video/MP2T'
                    elif fname.endswith('.jpg') or fname.endswith('.jpeg'): ct = 'image/jpeg'
                    elif fname.endswith('.webp'): ct = 'image/webp'
                    elif fname.endswith('.png'): ct = 'image/png'
                    elif fname.endswith('.json'): ct = 'application/json'
                    elif fname.endswith('.mp4'): ct = 'video/mp4'
                    
                    try:
                        s3.upload_file(local_path, BUCKET, r2_key, ExtraArgs={'ContentType': ct})
                        uploaded += 1
                        if uploaded % 50 == 0:
                            print(f'       Uploaded {uploaded} files...')
                    except Exception as e:
                        print(f'       ❌ {r2_key}: {str(e)[:50]}')
            
            print(f'     ✅ Re-uploaded {uploaded} files')

# STEP 3: Full R2 audit for ALL active dramas in DB
print(f'\n{"="*70}')
print('  STEP 3: FULL R2 AUDIT FOR ALL ACTIVE DRAMAS')
print('='*70)

# Get all active dramas from DB
r = requests.get('http://localhost:3001/api/dramas?limit=300', timeout=10)
db_dramas = r.json().get('dramas', [])
print(f'\n  Active dramas in DB: {len(db_dramas)}\n')

complete = 0
partial = 0
broken = 0
results = []

for d in sorted(db_dramas, key=lambda x: x.get('title', '')):
    title = d.get('title', '?')
    cover = d.get('cover', '')
    drama_id = d.get('id', '')
    total_eps = d.get('totalEpisodes', 0)
    
    # Extract R2 slug from cover URL
    match = re.search(r'melolo/([^/]+)/', cover)
    if not match:
        results.append(('❌', title, 'No R2 slug in cover URL', 0, 0))
        broken += 1
        continue
    
    slug = match.group(1)
    prefix = f'melolo/{slug}/'
    
    # Count files on R2
    r2_files = []
    continuation = None
    while True:
        kwargs = {'Bucket': BUCKET, 'Prefix': prefix, 'MaxKeys': 1000}
        if continuation:
            kwargs['ContinuationToken'] = continuation
        resp = s3.list_objects_v2(**kwargs)
        r2_files.extend(resp.get('Contents', []))
        if not resp.get('IsTruncated'):
            break
        continuation = resp.get('NextContinuationToken')
    
    total_size = sum(f['Size'] for f in r2_files) if r2_files else 0
    
    # Count unique episodes on R2
    ep_numbers = set()
    for f in r2_files:
        key = f['Key']
        rel = key[len(prefix):]
        
        # ep001/, ep002/ pattern
        m = re.match(r'ep(\d+)/', rel)
        if m:
            ep_numbers.add(int(m.group(1)))
            continue
        
        # episodes/001/ pattern
        m = re.match(r'episodes/(\d+)/', rel)
        if m:
            ep_numbers.add(int(m.group(1)))
            continue
        
        # Numeric dirs: 1/, 2/
        m = re.match(r'(\d+)/', rel)
        if m and int(m.group(1)) > 0:
            ep_numbers.add(int(m.group(1)))
    
    r2_eps = len(ep_numbers)
    size_mb = total_size / 1024 / 1024
    
    if r2_eps >= total_eps and total_eps > 0:
        status = '✅'
        complete += 1
    elif r2_eps > 0:
        status = '⚠️'
        partial += 1
    else:
        status = '❌'
        broken += 1
    
    results.append((status, title, slug, r2_eps, total_eps, size_mb, len(r2_files)))

# Print results
print(f'\n  {"Status":<4} {"Title":<45} {"R2eps":>6} {"DBeps":>6} {"Size":>8} {"Files":>6}')
print(f'  {"-"*4} {"-"*45} {"-"*6} {"-"*6} {"-"*8} {"-"*6}')

for r in results:
    if len(r) == 7:
        status, title, slug, r2_eps, total_eps, size_mb, files = r
        print(f'  {status:<4} {title[:45]:<45} {r2_eps:>6} {total_eps:>6} {size_mb:>7.1f}M {files:>6}')
    else:
        status, title, msg, _, _ = r
        print(f'  {status:<4} {title[:45]:<45} {msg}')

# Summary
total_files = sum(r[6] for r in results if len(r) == 7)
total_size = sum(r[5] for r in results if len(r) == 7)
total_r2_eps = sum(r[3] for r in results if len(r) == 7)

print(f'\n{"="*70}')
print(f'  AUDIT SUMMARY')
print(f'{"="*70}')
print(f'  ✅ Complete:  {complete} dramas')
print(f'  ⚠️ Partial:   {partial} dramas')
print(f'  ❌ Broken:    {broken} dramas')
print(f'  📊 R2 total:  {total_files:,} files, {total_size:,.1f} MB')
print(f'  📊 R2 eps:    {total_r2_eps:,} episodes detected')

# Save report
with open('r2_full_audit.txt', 'w', encoding='utf-8') as f:
    f.write(f'R2 Full Audit Report\n{"="*60}\n\n')
    for r in results:
        if len(r) == 7:
            status, title, slug, r2_eps, total_eps, size_mb, files = r
            f.write(f'{status} {title} | R2:{r2_eps}/{total_eps} eps | {size_mb:.1f}MB | {files} files | slug:{slug}\n')
        else:
            f.write(f'{r[0]} {r[1]} | {r[2]}\n')
    f.write(f'\nComplete: {complete}, Partial: {partial}, Broken: {broken}\n')
    f.write(f'Total: {total_files:,} files, {total_size:,.1f} MB, {total_r2_eps:,} episodes\n')

print(f'\n  Report saved to r2_full_audit.txt')
