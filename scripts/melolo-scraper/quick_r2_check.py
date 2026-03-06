#!/usr/bin/env python3
"""Quick R2 check: find dramas with 0 episodes on R2."""
import boto3, os, requests, json
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client('s3',
    endpoint_url=os.getenv('R2_ENDPOINT'),
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
    region_name='auto'
)
BUCKET = 'shortlovers'
BACKEND = 'http://localhost:3001/api'

# 1. Get all dramas from R2
print("📡 Scanning R2 for all drama folders...")
r2_dramas = {}
paginator = s3.get_paginator('list_objects_v2')

for page in paginator.paginate(Bucket=BUCKET, Prefix='melolo/', Delimiter='/'):
    for prefix in page.get('CommonPrefixes', []):
        slug = prefix['Prefix'].split('/')[1]
        if slug:
            r2_dramas[slug] = {'mp4': 0, 'hls': 0, 'cover': False}

print(f"   Found {len(r2_dramas)} drama folders on R2\n")

# 2. Count episodes per drama
print("🔍 Counting episodes per drama...")
for i, slug in enumerate(sorted(r2_dramas.keys()), 1):
    prefix = f"melolo/{slug}/"
    mp4_count = 0
    hls_eps = set()
    has_cover = False

    for page in paginator.paginate(Bucket=BUCKET, Prefix=prefix):
        for obj in page.get('Contents', []):
            key = obj['Key']
            rel = key[len(prefix):]
            if rel.endswith('.mp4'):
                mp4_count += 1
            elif rel.startswith('episodes/') and rel.endswith('.m3u8'):
                ep = rel.split('/')[1]
                hls_eps.add(ep)
            elif rel.startswith('cover'):
                has_cover = True

    r2_dramas[slug] = {'mp4': mp4_count, 'hls': len(hls_eps), 'cover': has_cover}
    total = mp4_count + len(hls_eps)
    status = "✅" if total > 0 else "❌"
    if i % 20 == 0 or total == 0:
        print(f"  [{i}/{len(r2_dramas)}] {slug}: {total} eps {status}")

# 3. Get DB dramas
print("\n📊 Fetching dramas from backend DB...")
db_dramas = {}
try:
    r = requests.get(f"{BACKEND}/dramas?limit=500", timeout=10)
    if r.status_code == 200:
        data = r.json()
        items = data if isinstance(data, list) else data.get('dramas', [])
        for d in items:
            db_dramas[d['title']] = {
                'id': d['id'],
                'totalEpisodes': d.get('totalEpisodes', 0),
                'provider': d.get('provider', ''),
            }
    print(f"   Found {len(db_dramas)} dramas in DB")
except Exception as e:
    print(f"   ⚠️ Backend error: {e}")

# 4. Report
print("\n" + "=" * 70)
print("  R2 EPISODE STATUS REPORT")
print("=" * 70)

no_eps = []
partial = []
ok = []

for slug, info in sorted(r2_dramas.items()):
    total = info['mp4'] + info['hls']
    if total == 0:
        no_eps.append((slug, info))
    elif not info['cover']:
        partial.append((slug, info, 'no cover'))
    else:
        ok.append((slug, info))

print(f"\n✅ Complete: {len(ok)} dramas")
print(f"⚠️  Partial:  {len(partial)} dramas")
print(f"❌ No episodes: {len(no_eps)} dramas")

if no_eps:
    print(f"\n{'─' * 70}")
    print(f"  ❌ DRAMAS WITH ZERO EPISODES ON R2 ({len(no_eps)})")
    print(f"{'─' * 70}")
    for slug, info in no_eps:
        cover = "🖼️" if info['cover'] else "  "
        print(f"  {cover} {slug}")

if partial:
    print(f"\n{'─' * 70}")
    print(f"  ⚠️ PARTIAL DRAMAS ({len(partial)})")
    print(f"{'─' * 70}")
    for slug, info, issue in partial:
        total = info['mp4'] + info['hls']
        print(f"  {slug}: {total} eps, {issue}")

# Summary
print(f"\n{'=' * 70}")
print(f"  TOTAL: {len(r2_dramas)} on R2, {len(db_dramas)} in DB")
print(f"  OK: {len(ok)} | Partial: {len(partial)} | No episodes: {len(no_eps)}")
print(f"{'=' * 70}")
