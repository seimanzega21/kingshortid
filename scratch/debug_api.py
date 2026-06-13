# -*- coding: utf-8 -*-
import sys; sys.stdout.reconfigure(encoding='utf-8')
import requests, json

API_BASE  = 'https://api.shortlovers.id/api'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

# Try several possible endpoints
endpoints_to_try = [
    '/dramas?limit=100',
    '/dramas?page=1&limit=100',
    '/admin/dramas?page=1&limit=100',
    '/dramas',
]

for ep in endpoints_to_try:
    url = API_BASE + ep
    r = requests.get(url, headers=ADMIN_HDR, timeout=15)
    print(f"GET {url} -> {r.status_code}")
    if r.ok:
        data = r.json()
        dramas = data if isinstance(data, list) else data.get('dramas', data.get('data', []))
        print(f"  Found {len(dramas)} dramas")
        for d in dramas[:5]:
            did   = d.get('id','?')
            title = d.get('title','?')
            print(f"    [{did}] {title}")
        break

# Also try direct drama endpoint
print("\n--- Direct lookup for known IDs ---")
for drama_id in ['lsr7c0n1qxnrfse46j86n88e']:
    for path in [f'/dramas/{drama_id}', f'/admin/dramas/{drama_id}']:
        r = requests.get(API_BASE + path, headers=ADMIN_HDR, timeout=10)
        print(f"  {path} -> {r.status_code}")
        if r.ok:
            d = r.json()
            print(f"    Title: {d.get('title')}, episodes: {d.get('totalEpisodes')}")
