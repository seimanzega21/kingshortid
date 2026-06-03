import requests
import json

API_BASE = 'https://api.shortlovers.id'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

queries = ["Mendengar", "Hati", "Hearing", "Heart"]
for q in queries:
    r = requests.get(f"{API_BASE}/api/dramas?search={q}", timeout=10)
    if r.ok:
        data = r.json()
        dramas = data if isinstance(data, list) else data.get('dramas', [])
        print(f"Query '{q}' returned {len(dramas)} dramas:")
        for d in dramas[:5]:
            print(f"  - Title: {d.get('title')} (ID: {d.get('id')})")
    else:
        print(f"Query '{q}' failed: {r.status_code}")
