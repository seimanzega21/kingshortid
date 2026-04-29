import requests, json
API_BASE = 'https://api.shortlovers.id'
drama_id = 'xt89nvjhqdkxlsc6gpz8csrl'
r = requests.get(f'{API_BASE}/api/dramas/{drama_id}')
if r.ok:
    data = r.json()
    # Print the whole drama object minus episodes for brevity
    eps = data.pop('episodes', [])
    print(json.dumps(data, indent=2))
