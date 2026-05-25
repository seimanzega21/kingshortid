import requests

API_BASE = 'https://api.shortlovers.id'
DRAMA_ID = 'byv3jp8t6vuqbnyxhfk08qlk'

# Get all episodes using public endpoint
r = requests.get(f'{API_BASE}/api/dramas/{DRAMA_ID}?includeInactive=true')
data = r.json()
eps = data.get('episodes', [])
print(f"Found {len(eps)} episodes")

for ep in sorted(eps, key=lambda x: x.get('episodeNumber', 0)):
    ep_id = ep['id']
    ep_num = ep['episodeNumber']
    r2 = requests.get(f'{API_BASE}/api/episodes/{ep_id}/subtitles')
    subs = r2.json().get('subtitles', [])
    print(f"EP {ep_num} ({ep_id}): {len(subs)} subtitles")
    if ep_num == 1 and subs:
        print(f"  EP 1 Subs: {subs}")
