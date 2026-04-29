import requests
API_BASE = 'https://api.shortlovers.id'
drama_id = 'yro6ngxolkb09mqdw19ejp1x'
r = requests.get(f'{API_BASE}/api/dramas/{drama_id}')
if r.ok:
    data = r.json()
    print(f"Title: {data.get('title')}")
    eps = data.get('episodes', [])
    for e in eps:
        if e['episodeNumber'] in [3, 5]:
            print(f"  Ep {e['episodeNumber']}: {e['videoUrl']}")
