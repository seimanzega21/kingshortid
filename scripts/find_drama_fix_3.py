import requests
API_BASE = 'https://api.shortlovers.id'
title = 'Putri'
r = requests.get(f'{API_BASE}/api/dramas?q={title}&limit=50')
if r.ok:
    data = r.json()
    for d in data.get('dramas', []):
        if 'Putri' in d['title']:
            print(f"ID: {d['id']}, Title: {d['title']}")
