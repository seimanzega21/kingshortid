import requests
API_BASE = 'https://api.shortlovers.id'
title = 'Putri Asli Kembali, Membalas Semuanya'
r = requests.get(f'{API_BASE}/api/dramas?q={title}&limit=5')
if r.ok:
    data = r.json()
    for d in data.get('dramas', []):
        print(f"ID: {d['id']}, Title: {d['title']}")
        # Get episodes
        dr = requests.get(f"{API_BASE}/api/dramas/{d['id']}")
        if dr.ok:
            eps = dr.json().get('episodes', [])
            for e in eps:
                if e['episodeNumber'] in [3, 5]:
                    print(f"  Ep {e['episodeNumber']}: {e['videoUrl']}")
else:
    print(f"Error: {r.status_code}")
