import requests
import json

API_BASE = 'https://api.shortlovers.id/api'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
headers = {'x-admin-key': ADMIN_KEY}

# Fetch all dramas
url = f"{API_BASE}/dramas?limit=1500&includeInactive=true"
r = requests.get(url, headers=headers)
if r.ok:
    dramas = r.json()
    if isinstance(dramas, dict):
        dramas = dramas.get("dramas", [])
    print(f"Total dramas in DB: {len(dramas)}")
    
    matches = [d for d in dramas if 'mafia' in d.get('title', '').lower()]
    print(f"Matches for 'mafia' ({len(matches)}):")
    for m in matches:
        print(f"  - {m.get('title')} (ID: {m.get('id')})")
else:
    print(f"Failed to fetch dramas: {r.status_code}")
