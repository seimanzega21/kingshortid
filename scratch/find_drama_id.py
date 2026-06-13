# -*- coding: utf-8 -*-
"""
Find the correct drama ID for 'Aku Terlahir Terlalu Patuh'
by looking up one of its known episode IDs and tracing back to drama ID.
"""
import sys; sys.stdout.reconfigure(encoding='utf-8')
import requests, json

API_BASE  = 'https://api.shortlovers.id/api'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

# Known episode IDs from the audit (EP 1-21) for drama lsr7c0n1qxnrfse46j86n88e
# Also known episode IDs for the "new" drama (EP 1-30 all YES) from second audit
# Second audit ep IDs: c4wbw3q4hvsv0g13683f5ftd (EP1), h8ecd3c9venv9szrt286gc0f (EP2), etc.
known_ep_ids = [
    'c4wbw3q4hvsv0g13683f5ftd',  # EP1 from new drama (second audit)
    'ntrj7uc8lujxbuo7ngjrmv76',  # EP1 from old drama (first audit)
]

print("--- Checking episode IDs to find drama IDs ---\n")
for ep_id in known_ep_ids:
    r = requests.get(f'{API_BASE}/episodes/{ep_id}', headers=ADMIN_HDR, timeout=15)
    print(f"EP ID: {ep_id} -> status={r.status_code}")
    if r.ok:
        data = r.json()
        print(f"  Data: {json.dumps(data, ensure_ascii=False)[:300]}")

# Try to search using the drama title directly using the search endpoint (different approach)
print("\n--- Search by title (various attempts) ---")
for q in ['Aku Terlahir', 'Terlalu Patuh', 'terlalu patuh']:
    r = requests.get(f'{API_BASE}/dramas/search?q={requests.utils.quote(q)}', headers=ADMIN_HDR, timeout=20)
    print(f"Search '{q}': status={r.status_code}")
    if r.ok:
        data = r.json()
        dramas = data if isinstance(data, list) else data.get('dramas', [])
        for d in dramas:
            title = d.get('title','')
            if 'patuh' in title.lower():
                print(f"  MATCH: [{d.get('id')}] {title} | active={d.get('isActive')} | eps={d.get('totalEpisodes')}")

# Try the fix_patuh log to see what drama_id was used
print("\n--- Reading fix_patuh2.log for drama ID ---")
try:
    with open(r'D:\kingshortid\scratch\fix_patuh2.log', encoding='utf-8') as f:
        for line in f:
            if 'registered' in line.lower() or 'drama db id' in line.lower() or 'drama id' in line.lower():
                print(f"  {line.strip()}")
except Exception as e:
    print(f"  Error: {e}")
