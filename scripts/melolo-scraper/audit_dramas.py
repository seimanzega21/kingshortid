#!/usr/bin/env python3
"""
Sample R2 file structure for a few dramas to understand naming patterns.
Then run full audit with corrected detection.
"""
import os, json, re, requests, boto3
from pathlib import Path
from collections import Counter
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
base = 'r2_ready/melolo'

# Step 1: Sample 3 dramas to understand R2 file structure
print("="*70)
print("  STEP 1: Sampling R2 file structure")
print("="*70)

samples = ['aku-kaya-dari-giok', 'cinta-sang-komandan', 'dari-miskin-jadi-sultan']

for slug in samples:
    prefix = f'melolo/{slug}/'
    print(f"\n--- {slug} ---")
    files = []
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=BUCKET, Prefix=prefix, PaginationConfig={'MaxItems': 500}):
        for obj in page.get('Contents', []):
            files.append(obj['Key'])
    
    print(f"  Total files: {len(files)}")
    
    # Show first 30 files to see pattern
    for f in sorted(files)[:30]:
        print(f"    {f}")
    if len(files) > 30:
        print(f"    ... ({len(files) - 30} more)")
    
    # Analyze extensions
    exts = Counter(f.split('.')[-1] for f in files if '.' in f.split('/')[-1])
    print(f"  Extensions: {dict(exts)}")
    
    # Analyze directory depth / path patterns
    depths = Counter(len(f.split('/')) for f in files)
    print(f"  Path depths: {dict(depths)}")
    
    # Try to find episode patterns
    ep_patterns = set()
    for f in files:
        parts = f.replace(prefix, '').split('/')
        if len(parts) >= 1:
            ep_patterns.add(parts[0])
    
    print(f"  Top-level items under {slug}/: {sorted(list(ep_patterns))[:20]}")

# Step 2: Full audit with corrected patterns
print(f"\n\n{'='*70}")
print(f"  STEP 2: Full audit with corrected detection")
print(f"{'='*70}\n")

# Get DB titles
r = requests.get('http://localhost:3001/api/dramas?limit=300', timeout=10)
db_titles = set(d.get('title','') for d in r.json().get('dramas', []))

results = []
out = open('audit_report.txt', 'w', encoding='utf-8')

def log(msg):
    print(msg, flush=True)
    out.write(msg + '\n')

idx = 0
for dirname in sorted(os.listdir(base)):
    dpath = os.path.join(base, dirname)
    if not os.path.isdir(dpath): continue
    meta_path = os.path.join(dpath, 'metadata.json')
    if not os.path.exists(meta_path): continue
    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    title = meta.get('title', dirname)
    if title in db_titles: continue
    
    idx += 1
    total_eps = meta.get('total_episodes', 0)
    fmt = meta.get('format', 'unknown')
    
    prefix = f'melolo/{dirname}/'
    r2_files = []
    try:
        paginator = s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=BUCKET, Prefix=prefix):
            for obj in page.get('Contents', []):
                r2_files.append({'key': obj['Key'], 'size': obj['Size']})
    except Exception as e:
        log(f"  [{idx:>2}] ❌ R2_ERROR  {title[:42]:<43} {str(e)[:40]}")
        results.append({'title': title, 'status': '❌ R2_ERROR', 'r2_eps': 0, 'total_eps': total_eps, 'r2_files': 0, 'r2_mb': 0, 'r2_covers': 0, 'dirname': dirname})
        continue
    
    r2_mb = sum(f['size'] for f in r2_files) / 1024 / 1024
    
    # Detect episodes using ALL possible patterns
    ep_numbers = set()
    has_cover = False
    has_metadata = False
    
    for f in r2_files:
        key = f['key']
        name = key.split('/')[-1]
        rel = key.replace(prefix, '')
        
        # Cover detection
        if any(x in name.lower() for x in ['cover', 'poster']):
            has_cover = True
        if name == 'metadata.json':
            has_metadata = True
        
        # Episode detection - multiple patterns:
        # 1. ep001.mp4, ep1.m3u8 (direct files)
        m = re.search(r'ep(\d+)', rel)
        if m:
            ep_numbers.add(int(m.group(1)))
            continue
        
        # 2. episode_001/..., episode-1/... (subdirectories)
        m = re.search(r'episode[_-]?(\d+)', rel)
        if m:
            ep_numbers.add(int(m.group(1)))
            continue
            
        # 3. Numeric folder names: 001/, 1/, etc (common HLS pattern)
        m = re.match(r'^(\d+)/', rel)
        if m and int(m.group(1)) > 0:
            ep_numbers.add(int(m.group(1)))
            continue
        
        # 4. .ts segment files with episode number in path
        m = re.search(r'(\d+)/.*\.ts$', rel)
        if m and int(m.group(1)) > 0:
            ep_numbers.add(int(m.group(1)))
            continue
        
        # 5. .m3u8 playlist files
        m = re.search(r'(\d+)/.*\.m3u8$', rel)
        if m and int(m.group(1)) > 0:
            ep_numbers.add(int(m.group(1)))
            continue
    
    # Status
    if total_eps > 0 and len(ep_numbers) >= total_eps:
        status = '✅ COMPLETE'
    elif len(ep_numbers) > 0 and total_eps > 0:
        pct = len(ep_numbers) / total_eps * 100
        status = f'⚠️ {pct:.0f}%'
    elif len(ep_numbers) > 0:
        status = '⚠️ PARTIAL'
    elif r2_mb > 1:
        status = '🟡 HAS_DATA'
    elif len(r2_files) > 0:
        status = '🟡 COVER'
    else:
        status = '❌ EMPTY'
    
    results.append({
        'title': title, 'dirname': dirname, 'status': status,
        'r2_eps': len(ep_numbers), 'total_eps': total_eps,
        'r2_files': len(r2_files), 'r2_mb': r2_mb,
        'r2_covers': 1 if has_cover else 0, 'format': fmt,
    })
    
    log(f"  [{idx:>2}] {status:<15} {title[:42]:<43} eps:{len(ep_numbers):>3}/{total_eps:<4} files:{len(r2_files):>5} ({r2_mb:>8.1f}MB) cover:{'✅' if has_cover else '❌'}")

# Summary
complete = [r for r in results if '✅' in r['status']]
partial = [r for r in results if '⚠️' in r['status']]
has_data = [r for r in results if '🟡' in r['status'] and 'HAS_DATA' in r['status']]
cover_only = [r for r in results if '🟡' in r['status'] and 'COVER' in r['status']]
empty = [r for r in results if '❌' in r['status']]

total_mb = sum(r['r2_mb'] for r in results)
total_eps_found = sum(r['r2_eps'] for r in results)
total_files = sum(r['r2_files'] for r in results)

log(f"\n{'='*70}")
log(f"  SUMMARY")
log(f"{'='*70}")
log(f"  Total non-DB dramas:      {len(results)}")
log(f"  ✅ Complete (all eps):     {len(complete)}")
log(f"  ⚠️ Partial (some eps):     {len(partial)}")
log(f"  🟡 Has data (undetected): {len(has_data)}")
log(f"  🟡 Cover only:            {len(cover_only)}")
log(f"  ❌ Empty/Error:           {len(empty)}")
log(f"")
log(f"  Total episodes detected:  {total_eps_found:,}")
log(f"  Total R2 files:           {total_files:,}")
log(f"  Total R2 size:            {total_mb:,.1f} MB ({total_mb/1024:.2f} GB)")

importable = [r for r in results if '✅' in r['status'] and r['r2_covers'] > 0]
log(f"\n  🚀 READY TO IMPORT: {len(importable)} dramas")

if complete:
    log(f"\n--- ✅ COMPLETE ({len(complete)}) ---")
    for r in complete:
        log(f"  {r['title'][:55]:<56} {r['r2_eps']:>3} eps  {r['r2_mb']:>8.1f}MB")

if partial:
    log(f"\n--- ⚠️ PARTIAL ({len(partial)}) ---")
    for r in partial:
        log(f"  {r['title'][:55]:<56} {r['r2_eps']:>3}/{r['total_eps']:<4} eps  {r['r2_mb']:>8.1f}MB  cover:{'✅' if r['r2_covers'] else '❌'}")

if has_data:
    log(f"\n--- 🟡 HAS DATA BUT NO EPISODE DETECTED ({len(has_data)}) ---")
    for r in has_data:
        log(f"  {r['title'][:55]:<56} {r['r2_files']:>5} files  {r['r2_mb']:>8.1f}MB")

out.close()
print("\n\nFull report saved to audit_report.txt")
