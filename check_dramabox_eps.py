import requests
API_BASE = 'http://141.11.160.187:3000'
drama_id = 'kjhmxxf2mk12ulrr7eqcyl8m'

r = requests.get(f'{API_BASE}/api/dramas/{drama_id}/episodes', timeout=15)
eps = sorted(r.json(), key=lambda x: int(x.get('episodeNumber', 0)))
print(f'Total eps in DB: {len(eps)}')
ep_nums = [int(e.get('episodeNumber', 0)) for e in eps]
print(f'Max episode: {max(ep_nums) if ep_nums else 0}')
print(f'Is ep 52 in DB: {52 in ep_nums}')
print('Last 3 episodes:')
for ep in eps[-3:]:
    num = ep.get('episodeNumber')
    url = ep.get('videoUrl', '')[:60]
    print(f'  EP{num} | {url}')
