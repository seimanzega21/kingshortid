import requests
API_BASE = 'https://api.shortlovers.id'
# Get all dramas (limit 200 for start)
r = requests.get(f'{API_BASE}/api/dramas?limit=500')
if r.ok:
    data = r.json()
    dramas = data.get('dramas', [])
    for d in dramas:
        if 'Putri' in d['title'] or 'Kembali' in d['title']:
            print(f"ID: {d['id']}, Title: {d['title']}")
