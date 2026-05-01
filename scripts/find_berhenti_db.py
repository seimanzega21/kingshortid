import requests

API_BASE = 'https://api.shortlovers.id'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

SEARCH = 'berhenti berjudi'

r = requests.get(f"{API_BASE}/api/dramas?limit=1000", headers=ADMIN_HDR, timeout=30)
if r.ok:
    for d in r.json().get('dramas', []):
        title = d.get('title','').lower()
        if SEARCH in title or 'utamakan keluarga' in title:
            print(f"FOUND: {d.get('title')}")
            print(f"  ID: {d.get('id')}")
            print(f"  totalEpisodes: {d.get('totalEpisodes')}")
            print(f"  isActive: {d.get('isActive')}")

# Also check by known ID pattern
print()
print('=== CHECK BY DIRECT ACCESS ===')
for db_id in ['r22zs10yvkmoq0vqn5sxofqz']:
    r = requests.get(f"{API_BASE}/api/dramas/{db_id}", headers=ADMIN_HDR, timeout=20)
    print(f"ID {db_id}: {r.status_code}")
