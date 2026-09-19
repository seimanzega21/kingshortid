import requests

API_BASE = 'https://api.shortlovers.id/api'
for title in ['Rubah Suci Pembawa Keberuntungan', 'Nama Terukir di Abu Kenangan']:
    r = requests.get(f'{API_BASE}/dramas?limit=1000&includeInactive=true')
    dramas = r.json().get('dramas', [])
    found = next((d for d in dramas if d['title'].lower() == title.lower()), None)
    if found:
        print(f"{title} -> ID: {found['id']}, totalEps: {found.get('totalEpisodes')}")
    else:
        print(f"{title} -> NOT FOUND in DB")
