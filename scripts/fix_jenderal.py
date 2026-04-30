"""Quick activate for a specific drama by ID."""
import requests
import time

ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
API_BASE = 'https://api.shortlovers.id'
HEADERS = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}
DRAMA_ID = 'dd0ztunafaosotezggkdqp0g'  # Jenderal, Masakanku Siap

res = requests.get(f'{API_BASE}/api/dramas/{DRAMA_ID}?includeInactive=true&_={int(time.time())}', headers=HEADERS).json()
eps = res.get('episodes', [])
inactive = [e for e in eps if not e['isActive']]
print(f'Found {len(eps)} eps, {len(inactive)} inactive. Activating...')

ok = 0
for ep in inactive:
    ep_id = ep['id']
    ep_num = ep['episodeNumber']
    r = requests.patch(f'{API_BASE}/api/episodes/{ep_id}', headers=HEADERS, json={'isActive': True})
    if r.status_code == 200:
        ok += 1
        print(f'  Ep {ep_num}: OK')
    elif r.status_code == 429:
        print(f'  Ep {ep_num}: rate limited, sleeping...')
        time.sleep(5)
    time.sleep(0.2)

print(f'\nDone: {ok}/{len(inactive)} activated')
