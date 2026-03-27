"""
Check if dubbed series covers are different from undubbed ones.
Some dubbed dramas might have Indonesian-captioned covers as their 
default cover (different UUID from the English original).

Also: compare current VPS cover UUIDs with what the API returns.
"""
import json, sys, re, requests
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from pathlib import Path
SCRIPT_DIR = Path(__file__).parent

# Load cached catalog
catalog = json.loads(open(SCRIPT_DIR / 'dubbed_metadata_cache.json', 'r', encoding='utf-8').read())
series = json.loads(open(SCRIPT_DIR / 'freereels_series_ids.json', 'r', encoding='utf-8').read())

print(f"{'='*60}")
print(f"  Comparing Dubbed vs Undubbed Cover UUIDs")
print(f"{'='*60}\n")

def extract_uuid(url):
    m = re.search(r'/cover/([a-f0-9-]{36})', url)
    return m.group(1) if m else ''

# Group series by episode count to find paired dubbed/undubbed versions
ep_groups = {}
for sid, sdata in series.items():
    if not isinstance(sdata, dict): continue
    cover = sdata.get('cover', '')
    ep_count = sdata.get('ep_count', 0)
    if ep_count not in ep_groups:
        ep_groups[ep_count] = []
    ep_groups[ep_count].append({'sid': sid, 'cover': cover, 'name': sdata.get('name', sid)})

# Check dubbed catalog entries to see if they have unique covers
print(f"  Dubbed catalog: {len(catalog)} entries")
print(f"\n  Checking cover UUIDs for all dubbed dramas:")

for entry in sorted(catalog, key=lambda x: x['ep_count']):
    cover_uuid = extract_uuid(entry['cover'])
    name = entry['name']
    ep_count = entry['ep_count']
    
    # Check if cover is accessible
    try:
        r = requests.head(entry['cover'], timeout=3, allow_redirects=True)
        status = r.status_code
    except:
        status = 0
    
    print(f"  {name[:40]:40s} | {ep_count:3d} eps | uuid={cover_uuid[:12]}... | {'✅' if status == 200 else '❌'}")

# Now let's look at the actual cover URLs from the browser subagent
# and check if ANY match entries in the series JSON
print(f"\n\n  Looking for Indonesian cover UUIDs in series JSON...")
browser_uuids = [
    'cd4038ca-589d-42c4-96a9-c3fe41fb8dbc',
    '09be9dcd-9b06-45ad-a27a-7b4a637866e9',
    '004fbf9a-a15d-4e12-92e0-84f8e41df1c2',
    '1978a654-c8fd-4cf5-9495-1d0e7a2e3172',
    'f4d9866e-5224-4ffd-b8f6-72367d63b173',
    'e6dd6d6a-74f3-400c-af9a-91ec8dc6d80a',
    'b87c1175-0cf8-4d9c-98bd-890e6ad19d77',
    'a2b1757b-867a-431c-934f-2bf5db9a3d8f',
    'c01efde2-dd40-4010-b6ef-13fb18ecd87f',
    '20d0d985-53ea-4fe9-8b50-36e00242c519',
    '98bdc916-9763-4e82-a93b-211c500f8ad6',
    'ee8589a5-7a3f-4db0-9d34-4fa4a8406320',
    '1bdfd5f4-553a-41b3-ad6d-e148bc8d01be',
]

# Check which browser UUIDs match actual series covers
for uuid in browser_uuids:
    for sid, sdata in series.items():
        if not isinstance(sdata, dict): continue
        if uuid in sdata.get('cover', ''):
            print(f"  ✅ {uuid[:12]}... → {sdata.get('name', sid)[:30]} (sid={sid})")
            break
    else:
        # Check in catalog
        for entry in catalog:
            if uuid in entry.get('cover', ''):
                print(f"  ✅ {uuid[:12]}... → {entry['name'][:30]} (from catalog)")
                break
        else:
            # Verify URL works
            url = f"https://static-v1.mydramawave.com/vt/prod/cover/{uuid}.jpg"
            try:
                r = requests.head(url, timeout=3, allow_redirects=True)
                print(f"  ? {uuid[:12]}... → NOT in series/catalog but HTTP {r.status_code}")
            except:
                print(f"  ❌ {uuid[:12]}... → NOT found anywhere")
