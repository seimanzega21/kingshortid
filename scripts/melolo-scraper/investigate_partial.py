#!/usr/bin/env python3
"""
Investigate partial dramas in R2:
1. List all 97 partial dramas (cover but no episodes)
2. Check if Vidrama API actually has episodes for them
3. Check if they exist in the backend database
"""
import boto3, os, json, requests, time
from dotenv import load_dotenv
load_dotenv()

s3 = boto3.client('s3',
    endpoint_url=os.getenv('R2_ENDPOINT'),
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'))
bucket = os.getenv('R2_BUCKET_NAME')

API_URL = "https://vidrama.asia/api/melolo"
BACKEND_URL = "http://localhost:3001/api"

# Step 1: Get all drama folders from R2 with their status
print("=" * 60)
print("  INVESTIGATING PARTIAL DRAMAS IN R2")
print("=" * 60)
print("\nScanning R2...", flush=True)

slugs = {}
paginator = s3.get_paginator('list_objects_v2')
for page in paginator.paginate(Bucket=bucket, Prefix='melolo/'):
    for obj in page.get('Contents', []):
        parts = obj['Key'].split('/')
        if len(parts) >= 2:
            sl = parts[1]
            if not sl or sl.startswith('_'):
                continue
            if sl not in slugs:
                slugs[sl] = {'eps': 0, 'cover': False, 'meta': False, 'files': []}
            if obj['Key'].endswith('.mp4'):
                slugs[sl]['eps'] += 1
            elif 'cover' in obj['Key']:
                slugs[sl]['cover'] = True
            elif 'metadata' in obj['Key']:
                slugs[sl]['meta'] = True

# Separate partial vs complete
partial = {sl: info for sl, info in slugs.items() if info['eps'] == 0}
complete = {sl: info for sl, info in slugs.items() if info['eps'] > 0}

print(f"\nTotal R2 dramas: {len(slugs)}")
print(f"Complete (has episodes): {len(complete)}")
print(f"Partial (0 episodes): {len(partial)}")

# Step 2: Load drama mapping to get titles
print("\n\nLoading drama discovery data...", flush=True)
try:
    with open("vidrama_all_dramas.json", "r", encoding="utf-8") as f:
        all_dramas = json.load(f)
    # Build slug->title mapping
    import re
    def slugify(text):
        text = text.lower().strip()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[\s_]+', '-', text)
        return re.sub(r'-+', '-', text).strip('-')
    
    slug_to_drama = {}
    for d in all_dramas:
        sl = slugify(d['title'])
        slug_to_drama[sl] = d
except:
    slug_to_drama = {}

# Step 3: Check backend database
print("Checking backend database...", flush=True)
db_titles = set()
db_dramas = {}
try:
    r = requests.get(f"{BACKEND_URL}/dramas?limit=1000", timeout=10)
    if r.status_code == 200:
        data = r.json()
        items = data if isinstance(data, list) else data.get("dramas", [])
        for d in items:
            db_titles.add(d.get("title", ""))
            db_dramas[d.get("title", "")] = d.get("id", "")
        print(f"  Database has {len(db_titles)} dramas")
    else:
        print(f"  Backend returned {r.status_code}")
except Exception as e:
    print(f"  Backend offline or error: {e}")

# Step 4: Print partial dramas with details
print("\n" + "=" * 60)
print("  PARTIAL DRAMAS (cover only, 0 episodes in R2)")
print("=" * 60)

partial_list = []
for sl in sorted(partial.keys()):
    drama = slug_to_drama.get(sl, {})
    title = drama.get('title', sl)
    drama_id = drama.get('id', '?')
    in_db = "YES" if title in db_titles else "NO"
    partial_list.append({
        'slug': sl,
        'title': title,
        'id': drama_id,
        'in_db': in_db,
        'cover': partial[sl]['cover'],
        'meta': partial[sl]['meta'],
    })

for i, p in enumerate(partial_list, 1):
    db_status = "DB:YES" if p['in_db'] == "YES" else "DB:NO"
    print(f"  {i:3}. {p['title'][:50]:<50} [{db_status}]")

# Summary
in_db_count = sum(1 for p in partial_list if p['in_db'] == "YES")
not_in_db = sum(1 for p in partial_list if p['in_db'] == "NO")
print(f"\n  Summary:")
print(f"    In database: {in_db_count}")
print(f"    NOT in database: {not_in_db}")

# Step 5: Spot-check 5 partial dramas against Vidrama API
print("\n" + "=" * 60)
print("  API SPOT-CHECK (testing 5 partial dramas)")
print("=" * 60)

checked = 0
for p in partial_list[:5]:
    if p['id'] == '?':
        print(f"\n  {p['slug']}: No drama ID found in discovery data")
        continue
    try:
        r = requests.get(f"{API_URL}?action=detail&id={p['id']}", timeout=10)
        if r.status_code == 200:
            detail = r.json().get("data", {})
            eps = detail.get("episodes", [])
            print(f"\n  {p['title'][:40]}:")
            print(f"    API episodes: {len(eps)}")
            if eps:
                print(f"    First ep: {eps[0].get('episodeNumber', '?')}")
                print(f"    Last ep: {eps[-1].get('episodeNumber', '?')}")
            else:
                print(f"    --> API CONFIRMS: No episodes available")
        else:
            print(f"\n  {p['title'][:40]}: API returned {r.status_code}")
        time.sleep(0.5)
    except Exception as e:
        print(f"\n  {p['title'][:40]}: Error - {e}")
    checked += 1

# Also check complete dramas in DB
print("\n" + "=" * 60)
print("  COMPLETE DRAMAS IN R2 - DB STATUS")
print("=" * 60)
complete_in_db = 0
complete_not_db = 0
for sl in sorted(complete.keys()):
    drama = slug_to_drama.get(sl, {})
    title = drama.get('title', sl)
    if title in db_titles:
        complete_in_db += 1
    else:
        complete_not_db += 1

print(f"  Complete dramas in R2: {len(complete)}")
print(f"  Registered in DB: {complete_in_db}")
print(f"  NOT in DB: {complete_not_db}")

# Save detailed report
report = {
    'partial_dramas': partial_list,
    'total_r2': len(slugs),
    'total_complete': len(complete),
    'total_partial': len(partial),
    'partial_in_db': in_db_count,
    'partial_not_in_db': not_in_db,
    'complete_in_db': complete_in_db,
    'complete_not_in_db': complete_not_db,
}
with open("vidrama_investigation.json", "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)
print(f"\n  Full report saved to vidrama_investigation.json")
