import requests

API_BASE = 'http://141.11.160.187:3000'
r = requests.get(f'{API_BASE}/api/dramas?limit=1000', timeout=30)
if r.ok:
    dramas = r.json()
    if isinstance(dramas, dict):
        dramas = dramas.get('dramas', [])
    for d in dramas:
        if 'cerai' in d.get('title', '').lower():
            print(f"ID: {d['id']}, Title: {d['title']}")
