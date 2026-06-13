# -*- coding: utf-8 -*-
import sys; sys.stdout.reconfigure(encoding='utf-8')
import requests, json

API_BASE  = 'https://api.shortlovers.id/api'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY}

# Check old drama ID
old_id = 'lsr7c0n1qxnrfse46j86n88e'
r = requests.get(f'{API_BASE}/dramas/{old_id}', headers=ADMIN_HDR, timeout=15)
print(f"Old drama ID status: {r.status_code}")
if r.ok:
    d = r.json()
    title = d.get('title')
    active = d.get('isActive')
    eps = d.get('totalEpisodes')
    print(f"  Title: {title}, isActive: {active}, totalEpisodes: {eps}")

# List all dramas
print("\n--- ALL DRAMAS IN ADMIN ---")
r2 = requests.get(f'{API_BASE}/admin/dramas?limit=100', headers=ADMIN_HDR, timeout=15)
print(f"Status: {r2.status_code}")
if r2.ok:
    data = r2.json()
    dramas = data if isinstance(data, list) else data.get('dramas', data.get('data', []))
    for d in dramas:
        did   = d.get('id')
        title = d.get('title')
        active = d.get('isActive')
        eps   = d.get('totalEpisodes')
        print(f"  [{did}] {title} | active={active} | eps={eps}")
