# -*- coding: utf-8 -*-
import sys; sys.stdout.reconfigure(encoding='utf-8')
import requests, json

API_BASE  = 'https://api.shortlovers.id/api'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

# Get ALL dramas - paginate
all_dramas = []
page = 1
while True:
    r = requests.get(f'{API_BASE}/dramas?limit=100&page={page}', headers=ADMIN_HDR, timeout=15)
    if not r.ok:
        break
    data = r.json()
    dramas = data if isinstance(data, list) else data.get('dramas', data.get('data', []))
    if not dramas:
        break
    all_dramas.extend(dramas)
    print(f"Page {page}: got {len(dramas)} dramas (total so far: {len(all_dramas)})")
    if len(dramas) < 100:
        break
    page += 1

print(f"\nTotal dramas: {len(all_dramas)}")
print("\n--- Searching for 'Patuh' ---")
for d in all_dramas:
    title = d.get('title', '')
    if 'patuh' in title.lower() or 'Patuh' in title:
        did   = d.get('id')
        active = d.get('isActive')
        eps   = d.get('totalEpisodes')
        print(f"  FOUND: [{did}] {title} | active={active} | eps={eps}")
