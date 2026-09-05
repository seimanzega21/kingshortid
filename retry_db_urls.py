import requests, time

API_BASE  = 'http://141.11.160.187:3000'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}
R2_PUBLIC   = 'https://stream.shortlovers.id'
DRAMA_ID_DB = 'kjhmxxf2mk12ulrr7eqcyl8m'
DRAMA_SLUG  = 'hati-yang-dihancurkan'

while True:
    er = requests.get(f"{API_BASE}/api/dramas/{DRAMA_ID_DB}/episodes", timeout=15)
    if er.ok and isinstance(er.json(), list):
        eps = sorted(er.json(), key=lambda x: int(x.get('episodeNumber', 0)))
        break
    time.sleep(2)

for ep in eps:
    if not isinstance(ep, dict): continue
    num = int(ep.get('episodeNumber'))
    ep_id = ep['id']
    
    # Check if already has v2
    if '_v2_' in ep.get('videoUrl', ''):
        continue

    url720 = f"{R2_PUBLIC}/dramas/{DRAMA_SLUG}/ep{num:03d}_v2_720p.mp4"
    url540 = f"{R2_PUBLIC}/dramas/{DRAMA_SLUG}/ep{num:03d}_v2_540p.mp4"
    
    payload = {
        'videoUrl': url720,
        'videoUrl540p': url540,
    }
    
    while True:
        upd = requests.patch(f"{API_BASE}/api/episodes/{ep_id}", headers=ADMIN_HDR, json=payload, timeout=20)
        if upd.ok:
            print(f"  ✅ DB Patched: EP{num}")
            break
        elif upd.status_code == 429:
            print(f"  ⏳ 429 Rate limited on EP{num}, waiting 2 seconds...")
            time.sleep(2)
        else:
            print(f"  ❌ DB Failed EP{num}: {upd.status_code} {upd.text[:40]}")
            break
