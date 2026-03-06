#!/usr/bin/env python3
"""R2 audit only — no re-uploads. Check all active DB dramas against R2."""
import os, json, re, boto3, requests
from dotenv import load_dotenv
from pathlib import Path
from botocore.config import Config

load_dotenv(Path(__file__).parent / '.env')
config = Config(retries={'max_attempts': 3}, connect_timeout=10, read_timeout=30)
s3 = boto3.client('s3',
    endpoint_url=os.getenv('R2_ENDPOINT'),
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
    region_name='auto', config=config)
BUCKET = 'shortlovers'

print('='*70)
print('  R2 AUDIT — ALL ACTIVE DRAMAS')
print('='*70)

r = requests.get('http://localhost:3001/api/dramas?limit=300', timeout=10)
db_dramas = r.json().get('dramas', [])
print(f'\n  Active dramas in DB: {len(db_dramas)}\n')

results = []
for i, d in enumerate(sorted(db_dramas, key=lambda x: x.get('title', '')), 1):
    title = d.get('title', '?')
    cover = d.get('cover', '')
    total_eps = d.get('totalEpisodes', 0)

    match = re.search(r'melolo/([^/]+)/', cover)
    if not match:
        results.append(('❌', title, '???', 0, total_eps, 0, 0))
        continue
    slug = match.group(1)
    prefix = f'melolo/{slug}/'

    # List all R2 files
    r2_files = []
    cont = None
    while True:
        kw = {'Bucket': BUCKET, 'Prefix': prefix, 'MaxKeys': 1000}
        if cont: kw['ContinuationToken'] = cont
        resp = s3.list_objects_v2(**kw)
        r2_files.extend(resp.get('Contents', []))
        if not resp.get('IsTruncated'): break
        cont = resp.get('NextContinuationToken')

    total_size = sum(f['Size'] for f in r2_files)
    ep_nums = set()
    for f in r2_files:
        rel = f['Key'][len(prefix):]
        m = re.match(r'ep(\d+)/', rel)
        if m: ep_nums.add(int(m.group(1))); continue
        m = re.match(r'episodes/(\d+)/', rel)
        if m: ep_nums.add(int(m.group(1))); continue
        m = re.match(r'(\d+)/', rel)
        if m and int(m.group(1)) > 0: ep_nums.add(int(m.group(1)))

    r2_eps = len(ep_nums)
    mb = total_size / 1024 / 1024

    if r2_eps >= total_eps and total_eps > 0:
        st = '✅'
    elif r2_eps > 0:
        st = '⚠️'
    elif len(r2_files) > 0:
        st = '🟡'
    else:
        st = '❌'

    results.append((st, title, slug, r2_eps, total_eps, mb, len(r2_files)))
    print(f'  [{i}/{len(db_dramas)}] {st} {title[:40]:<40} R2:{r2_eps}/{total_eps} eps  {mb:.0f}MB')

# Summary
complete = sum(1 for r in results if r[0] == '✅')
partial = sum(1 for r in results if r[0] == '⚠️')
cover_only = sum(1 for r in results if r[0] == '🟡')
empty = sum(1 for r in results if r[0] == '❌')
total_files = sum(r[6] for r in results)
total_mb = sum(r[5] for r in results)
total_r2_eps = sum(r[3] for r in results)

print(f'\n{"="*70}')
print(f'  AUDIT SUMMARY')
print(f'{"="*70}')
print(f'  ✅ Complete:    {complete}')
print(f'  ⚠️ Partial:     {partial}')
print(f'  🟡 Cover only:  {cover_only}')
print(f'  ❌ Empty/Error: {empty}')
print(f'  📊 R2 total:    {total_files:,} files, {total_mb:,.0f} MB')
print(f'  📊 R2 episodes: {total_r2_eps:,}')

# Print issues
issues = [r for r in results if r[0] != '✅']
if issues:
    print(f'\n  --- ISSUES ({len(issues)}) ---')
    for st, title, slug, r2e, dbe, mb, fc in issues:
        print(f'  {st} {title[:50]:<50} R2:{r2e}/{dbe} eps  {mb:.0f}MB  [{slug}]')

# Save report
with open('r2_full_audit.txt', 'w', encoding='utf-8') as f:
    for st, title, slug, r2e, dbe, mb, fc in results:
        f.write(f'{st} {title} | R2:{r2e}/{dbe} eps | {mb:.0f}MB | {fc} files | {slug}\n')
    f.write(f'\nComplete:{complete} Partial:{partial} CoverOnly:{cover_only} Empty:{empty}\n')
    f.write(f'Total: {total_files:,} files, {total_mb:,.0f} MB, {total_r2_eps:,} eps\n')
print(f'\n  Saved: r2_full_audit.txt')
