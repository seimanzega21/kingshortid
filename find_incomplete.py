import requests

API_BASE = 'http://141.11.160.187:3000'

r = requests.get(f'{API_BASE}/api/dramas?limit=5000', timeout=60)
data = r.json()
dramas = data if isinstance(data, list) else data.get('dramas', [])

keywords = ['jerat terlarang', 'legenda sang raja perang', 'bosku ternyata suami rahasia', 'aku mengikat dewi', 'dalam genggaman', 'tawanan hati sang raja serigala']

print(f'Total dramas in DB: {len(dramas)}')
print()
found = []
for d in dramas:
    t = d.get('title', '').lower().strip()
    for kw in keywords:
        if kw in t:
            found.append(d)
            print(f"ID: {d.get('id')} | Total: {d.get('totalEpisodes')} | Title: {d.get('title')}")

if not found:
    print("None found. Listing all dramas with 1 episode:")
    for d in dramas:
        if d.get('totalEpisodes', 99) <= 2:
            print(f"  {d.get('id')} | {d.get('totalEpisodes')} eps | {d.get('title', '')[:60]}")
