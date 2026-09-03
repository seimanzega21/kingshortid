import requests
API_BASE = 'http://141.11.160.187:3000'
r = requests.get(f'{API_BASE}/api/dramas?limit=5000', timeout=60)
data = r.json()
dramas = data if isinstance(data, list) else data.get('dramas', [])

targets = ['jerat terlarang sang profesor', 'legenda sang raja perang', 'bosku ternyata suami rahasiaku', 'aku mengikat dewi', 'dalam genggaman iparku', 'tawanan hati sang raja serigala']

print(f"Searching in {len(dramas)} dramas...\n")
for d in dramas:
    t = d.get('title','').lower().strip()
    for kw in targets:
        if kw[:15] in t:
            did = d['id']
            r2 = requests.get(f'{API_BASE}/api/dramas/{did}/episodes', timeout=15)
            ep_count = len(r2.json()) if r2.ok else '?'
            print(f"DB total: {d.get('totalEpisodes')} | Actual eps in DB: {ep_count} | {d.get('title')} | {did}")
            break
