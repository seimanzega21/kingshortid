import requests
import warnings
warnings.filterwarnings('ignore')

DRAMA_ID = '14pt69lgiygn834gag5nqse'
API = 'https://api.shortlovers.id/api'

# Load admin token from config
import os
token_path = os.path.join(os.path.dirname(__file__), '..', 'scripts', '.admin_token')
ADMIN_TOKEN = ''
if os.path.exists(token_path):
    with open(token_path) as f:
        ADMIN_TOKEN = f.read().strip()

HEADERS = {'Authorization': f'Bearer {ADMIN_TOKEN}'} if ADMIN_TOKEN else {}

print(f'Checking drama: {DRAMA_ID}')
r = requests.get(f'{API}/dramas/{DRAMA_ID}', headers=HEADERS, verify=False, timeout=15)
print(f'Status: {r.status_code}')

if not r.ok:
    print('ERROR:', r.text[:300])
    exit(1)

data = r.json()
print(f'Title: {data.get("title")}')
eps = data.get('episodes', [])
print(f'Episodes in response: {len(eps)}')

if not eps:
    print('No episodes found. Trying /dramas/{id}/episodes...')
    r2 = requests.get(f'{API}/dramas/{DRAMA_ID}/episodes', headers=HEADERS, verify=False, timeout=15)
    print(f'Episodes status: {r2.status_code}')
    print(r2.text[:500])
    exit(0)

# Check first 3 episodes for subtitles
print()
for ep in eps[:3]:
    ep_id = ep.get('id')
    ep_no = ep.get('episodeNumber')
    print(f'--- Episode {ep_no} (ID: {ep_id}) ---')
    print(f'  Subtitles in drama response: {ep.get("subtitles")}')
    
    # Direct subtitle fetch
    r_sub = requests.get(f'{API}/episodes/{ep_id}/subtitles', headers=HEADERS, verify=False, timeout=10)
    print(f'  Direct subtitle API: {r_sub.status_code}')
    sub_data = r_sub.json()
    subs = sub_data.get('subtitles', [])
    print(f'  Subtitle count: {len(subs)}')
    for s in subs:
        print(f'    - lang={s.get("language")} | url={s.get("url")[:80]}...')
    
    if not subs:
        print(f'  >> NO SUBTITLES in DB for this episode!')
    print()
