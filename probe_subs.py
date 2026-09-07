import requests

API_BASE = 'http://141.11.160.187:3000'
DRAMA_ID_DB = 'pblx23fpfucss8wmjk2f0n32'
BOOK_ID = '42000026716'
HDR = {'User-Agent': 'Mozilla/5.0'}

# 1. Check DB
er = requests.get(f'{API_BASE}/api/dramas/{DRAMA_ID_DB}/episodes', timeout=15)
eps = er.json()
ep_nums = [int(e.get('episodeNumber')) for e in eps]
missing = [i for i in range(1, 58) if i not in ep_nums]
print(f'Missing in DB: {missing}')

for ep in eps:
    if ep.get('episodeNumber') == 17:
        print(f"EP17 ID in DB: {ep.get('id')}")

# 2. Check Dramabox API
for api_ep in [16, 8, 9, 10]:
    r = requests.get(f'https://vidrama.asia/api/dramabox?action=stream&id={BOOK_ID}&episode={api_ep}&lang=in', headers=HDR)
    data = r.json().get('data', {})
    subs = data.get('subtitles', [])
    v_url = data.get('videoUrl') or data.get('rawVideoUrl')
    print(f'API Ep {api_ep} -> Video exists: {bool(v_url)}, Subs count: {len(subs)}')
    if subs:
        print(f'   Sub: {subs[0]}')
