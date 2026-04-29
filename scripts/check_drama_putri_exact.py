import requests
API_BASE = 'https://api.shortlovers.id'
drama_id = 'xt89nvjhqdkxlsc6gpz8csrl'
r = requests.get(f'{API_BASE}/api/dramas/{drama_id}')
if r.ok:
    data = r.json()
    eps = data.get('episodes', [])
    for e in eps:
        if e['episodeNumber'] in [3, 5]:
            print(f"Ep {e['episodeNumber']}: {e['videoUrl']}")
