#!/usr/bin/env python3
"""Compare local r2_ready vs what's actually on R2"""
import boto3, os, json, sys, io
from pathlib import Path
from dotenv import load_dotenv

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stdout.reconfigure(line_buffering=True)

load_dotenv(Path(__file__).parent / '.env')

s3 = boto3.client('s3',
    endpoint_url=os.getenv('R2_ENDPOINT'),
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
    region_name='auto'
)
bucket = os.getenv('R2_BUCKET_NAME', 'shortlovers')
melolo = Path(__file__).parent / 'r2_ready' / 'melolo'

# 1. Get all R2 drama prefixes and file counts
print("Scanning R2...")
r2_dramas = {}
paginator = s3.get_paginator('list_objects_v2')
for page in paginator.paginate(Bucket=bucket, Prefix='melolo/'):
    for obj in page.get('Contents', []):
        key = obj['Key']
        parts = key.split('/')
        if len(parts) >= 2:
            slug = parts[1]
            if slug not in r2_dramas:
                r2_dramas[slug] = {'files': 0, 'bytes': 0, 'has_meta': False, 'has_cover': False, 'eps': set()}
            r2_dramas[slug]['files'] += 1
            r2_dramas[slug]['bytes'] += obj['Size']
            if key.endswith('metadata.json'):
                r2_dramas[slug]['has_meta'] = True
            if key.endswith('cover.jpg'):
                r2_dramas[slug]['has_cover'] = True
            if '/ep' in key and key.endswith('.m3u8'):
                ep = parts[2] if len(parts) > 2 else ''
                r2_dramas[slug]['eps'].add(ep)

# 2. Get local drama stats
print("Scanning local...")
local_dramas = {}
for d in sorted(melolo.iterdir()):
    if not d.is_dir(): continue
    slug = d.name
    files = list(d.rglob('*'))
    file_count = sum(1 for f in files if f.is_file())
    ep_dirs = [e for e in d.iterdir() if e.is_dir() and e.name.startswith('ep')]
    m3u8s = sum(1 for f in files if f.is_file() and f.name == 'playlist.m3u8')
    local_dramas[slug] = {
        'files': file_count,
        'eps': len(ep_dirs),
        'hls': m3u8s,
        'has_meta': (d / 'metadata.json').exists(),
        'has_cover': (d / 'cover.jpg').exists(),
    }

# 3. Compare
print(f"\n{'='*70}")
print(f"  LOCAL vs R2 COMPARISON")
print(f"{'='*70}\n")

fully_on_r2 = 0
partial_r2 = 0
not_on_r2 = 0
missing_meta_r2 = []
missing_cover_r2 = []

for slug in sorted(local_dramas.keys()):
    loc = local_dramas[slug]
    r2 = r2_dramas.get(slug)
    
    if not r2 or r2['files'] == 0:
        not_on_r2 += 1
        if loc['hls'] > 0:
            print(f"  ❌ {slug}: {loc['files']} local files, NOT on R2")
    elif r2['files'] < loc['files']:
        partial_r2 += 1
        pct = (r2['files'] / loc['files'] * 100) if loc['files'] > 0 else 0
        print(f"  ⚠️  {slug}: {r2['files']}/{loc['files']} files ({pct:.0f}%)")
    else:
        fully_on_r2 += 1
    
    if r2 and not r2['has_meta'] and loc['has_meta']:
        missing_meta_r2.append(slug)
    if r2 and not r2['has_cover'] and loc['has_cover']:
        missing_cover_r2.append(slug)

print(f"\n{'='*70}")
print(f"  SUMMARY")
print(f"{'='*70}")
print(f"  Local dramas:        {len(local_dramas)}")
print(f"  Fully on R2:         {fully_on_r2} ✅")
print(f"  Partial on R2:       {partial_r2} ⚠️")
print(f"  Not on R2:           {not_on_r2} ❌")
print(f"  R2 dramas total:     {len(r2_dramas)}")
print(f"  R2 total files:      {sum(d['files'] for d in r2_dramas.values())}")
print(f"  R2 total size:       {sum(d['bytes'] for d in r2_dramas.values()) / (1024**3):.2f} GB")
if missing_meta_r2:
    print(f"  Missing metadata:    {len(missing_meta_r2)}")
if missing_cover_r2:
    print(f"  Missing covers:      {len(missing_cover_r2)}")
print(f"{'='*70}")
