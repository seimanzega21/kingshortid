#!/usr/bin/env python3
"""
Full R2 audit: count BOTH HLS (.m3u8/.ts) and MP4 files per drama
Also check backend database status
"""
import boto3, os, json, requests
from dotenv import load_dotenv
load_dotenv()

s3 = boto3.client('s3',
    endpoint_url=os.getenv('R2_ENDPOINT'),
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'))
bucket = os.getenv('R2_BUCKET_NAME')

BACKEND_URL = "http://localhost:3001/api"

print("=" * 65)
print("  FULL R2 AUDIT (HLS + MP4)")
print("=" * 65)
print("\nScanning R2 (this may take a minute)...", flush=True)

slugs = {}
total_files = 0
total_bytes = 0

paginator = s3.get_paginator('list_objects_v2')
for page in paginator.paginate(Bucket=bucket, Prefix='melolo/'):
    for obj in page.get('Contents', []):
        total_files += 1
        total_bytes += obj['Size']
        parts = obj['Key'].split('/')
        if len(parts) < 2:
            continue
        sl = parts[1]
        if not sl or sl.startswith('_'):
            continue
        if sl not in slugs:
            slugs[sl] = {
                'mp4': 0, 'hls_m3u8': 0, 'hls_ts': 0,
                'cover': False, 'meta': False, 'other': 0,
                'mp4_size': 0, 'hls_size': 0
            }
        key = obj['Key']
        size = obj['Size']
        if key.endswith('.mp4'):
            slugs[sl]['mp4'] += 1
            slugs[sl]['mp4_size'] += size
        elif key.endswith('.m3u8'):
            slugs[sl]['hls_m3u8'] += 1
            slugs[sl]['hls_size'] += size
        elif key.endswith('.ts'):
            slugs[sl]['hls_ts'] += 1
            slugs[sl]['hls_size'] += size
        elif 'cover' in key:
            slugs[sl]['cover'] = True
        elif 'metadata' in key:
            slugs[sl]['meta'] = True
        else:
            slugs[sl]['other'] += 1

# Categorize
mp4_only = []      # Has MP4 episodes only
hls_only = []      # Has HLS episodes only
both = []          # Has both MP4 and HLS
no_episodes = []   # Only cover/metadata, no video

for sl, info in sorted(slugs.items()):
    has_mp4 = info['mp4'] > 0
    has_hls = info['hls_ts'] > 0 or info['hls_m3u8'] > 0
    if has_mp4 and has_hls:
        both.append(sl)
    elif has_mp4:
        mp4_only.append(sl)
    elif has_hls:
        hls_only.append(sl)
    else:
        no_episodes.append(sl)

print(f"\n{'=' * 65}")
print(f"  SUMMARY")
print(f"{'=' * 65}")
print(f"  Total drama folders:    {len(slugs)}")
print(f"  Total files:            {total_files}")
print(f"  Total size:             {total_bytes/1024/1024/1024:.2f} GB")
print()
print(f"  MP4 only (Vidrama):     {len(mp4_only)}")
print(f"  HLS only (old scrape):  {len(hls_only)}")
print(f"  Both MP4+HLS:           {len(both)}")
print(f"  No episodes at all:     {len(no_episodes)}")

# Count total episodes
total_mp4 = sum(s['mp4'] for s in slugs.values())
total_m3u8 = sum(s['hls_m3u8'] for s in slugs.values())
total_ts = sum(s['hls_ts'] for s in slugs.values())
mp4_gb = sum(s['mp4_size'] for s in slugs.values()) / 1024/1024/1024
hls_gb = sum(s['hls_size'] for s in slugs.values()) / 1024/1024/1024
print()
print(f"  Total MP4 files:        {total_mp4} ({mp4_gb:.2f} GB)")
print(f"  Total M3U8 playlists:   {total_m3u8}")
print(f"  Total TS segments:      {total_ts} ({hls_gb:.2f} GB)")

# Check backend DB
print(f"\n{'=' * 65}")
print(f"  BACKEND DATABASE STATUS")
print(f"{'=' * 65}")
try:
    r = requests.get(f"{BACKEND_URL}/dramas?limit=1000", timeout=10)
    if r.status_code == 200:
        data = r.json()
        items = data if isinstance(data, list) else data.get("dramas", [])
        print(f"  Total dramas in DB:     {len(items)}")
        
        # Check how many match R2 slugs
        import re
        def slugify(text):
            text = text.lower().strip()
            text = re.sub(r'[^\w\s-]', '', text)
            text = re.sub(r'[\s_]+', '-', text)
            return re.sub(r'-+', '-', text).strip('-')
        
        db_slugs = {slugify(d.get("title", "")): d for d in items}
        
        in_r2_and_db = set(db_slugs.keys()) & set(slugs.keys())
        in_db_not_r2 = set(db_slugs.keys()) - set(slugs.keys())
        in_r2_not_db = set(slugs.keys()) - set(db_slugs.keys())
        
        print(f"  In both R2 + DB:        {len(in_r2_and_db)}")
        print(f"  In DB but not R2:       {len(in_db_not_r2)}")
        print(f"  In R2 but not DB:       {len(in_r2_not_db)}")
        
        # Check episode count per drama in DB
        total_db_eps = 0
        for d in items:
            ep_count = d.get("totalEpisodes", 0) or d.get("_count", {}).get("episodes", 0) or 0
            total_db_eps += ep_count
        print(f"  Total episodes in DB:   {total_db_eps}")
    else:
        print(f"  Backend returned: {r.status_code}")
except Exception as e:
    print(f"  Backend error: {e}")

# Print HLS-only dramas
if hls_only:
    print(f"\n{'=' * 65}")
    print(f"  HLS-ONLY DRAMAS ({len(hls_only)})")
    print(f"{'=' * 65}")
    for i, sl in enumerate(sorted(hls_only), 1):
        info = slugs[sl]
        ts_count = info['hls_ts']
        m3u8_count = info['hls_m3u8']
        size_mb = info['hls_size'] / 1024 / 1024
        print(f"  {i:3}. {sl:<45} {m3u8_count} m3u8, {ts_count} ts ({size_mb:.0f}MB)")

# Print no-episode dramas
if no_episodes:
    print(f"\n{'=' * 65}")
    print(f"  DRAMAS WITH NO EPISODES ({len(no_episodes)})")
    print(f"{'=' * 65}")
    for i, sl in enumerate(sorted(no_episodes), 1):
        info = slugs[sl]
        has = []
        if info['cover']:
            has.append("cover")
        if info['meta']:
            has.append("meta")
        print(f"  {i:3}. {sl:<45} [{', '.join(has)}]")

# Save full report
report = {
    "summary": {
        "total_dramas": len(slugs),
        "mp4_only": len(mp4_only),
        "hls_only": len(hls_only),
        "both": len(both),
        "no_episodes": len(no_episodes),
        "total_mp4_files": total_mp4,
        "total_ts_segments": total_ts,
        "total_m3u8": total_m3u8,
        "total_size_gb": round(total_bytes/1024/1024/1024, 2),
    },
    "mp4_only_slugs": mp4_only,
    "hls_only_slugs": hls_only,
    "both_slugs": both,
    "no_episode_slugs": no_episodes,
}
with open("r2_full_audit_result.json", "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)
print(f"\nFull report saved to r2_full_audit_result.json")
