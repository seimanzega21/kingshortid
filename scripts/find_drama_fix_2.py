import requests
API_BASE = 'https://api.shortlovers.id'
title = 'Putri Asli Kembali'
r = requests.get(f'{API_BASE}/api/dramas?q={title}&limit=10')
if r.ok:
    data = r.json()
    for d in data.get('dramas', []):
        print(f"ID: {d['id']}, Title: {d['title']}")
