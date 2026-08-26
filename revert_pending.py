import json
import requests

API_BASE  = 'http://141.11.160.187:3000'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

try:
    with open('new_netshort_dramas.json', 'r', encoding='utf-8') as f:
        queue = json.load(f)
except Exception:
    queue = []

updated = 0
for d in queue:
    # We can't search by slug directly on the admin list without knowing if it's there, but we can search by title.
    # Wait, the slug is known. The GET /api/dramas/{slug} works to find the ID.
    r = requests.get(f"{API_BASE}/api/dramas/{d['slug']}", timeout=10)
    if r.ok:
        drama = r.json()
        if drama and 'id' in drama:
            drama_id = drama['id']
            # update to pending
            payload = {'isActive': False, 'status': 'pending'}
            r_up = requests.put(f"{API_BASE}/api/admin/dramas/{drama_id}", headers=ADMIN_HDR, json=payload, timeout=10)
            if r_up.ok:
                print(f"Updated {d['slug']} to pending")
                updated += 1
                
print(f"Total updated: {updated}")
