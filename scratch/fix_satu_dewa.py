import sys
import requests
import time

admin_key = 'kngshrt_adm_9921_x'

with open('scripts/scrape_freereels_queue.py', 'r', encoding='utf-8') as f:
    for line in f:
        if 'ADMIN_KEY' in line and '=' in line and 'os.getenv' not in line:
            parts = line.split('=')
            if len(parts) >= 2:
                val = parts[1].split('#')[0].strip().strip('"').strip("'")
                if val:
                    admin_key = val
                    break

API_BASE = 'https://api.shortlovers.id/api'
ADMIN_HDR = {'x-admin-key': admin_key, 'Content-Type': 'application/json'}

db_id = 'dt9wnyumb4fj2i51p6r9kwds'
R2_PUBLIC = 'https://stream.shortlovers.id'
prefix = 'netshortv2/satu-dewa-perang-tujuh-ratu-versi-dub'

for ep in [33, 38]:
    u720 = f'{R2_PUBLIC}/{prefix}/ep{ep:03d}.mp4'
    u540 = f'{R2_PUBLIC}/{prefix}/ep{ep:03d}_540p.mp4'
    sub_url = f'{R2_PUBLIC}/{prefix}/ep{ep:03d}.vtt'
    
    payload = {
        'episodeNumber': ep,
        'videoUrl': u720,
        'videoUrl_540p': u540
    }
    
    print(f'Posting ep {ep}...')
    r = requests.post(f'{API_BASE}/admin/dramas/{db_id}/episodes', headers=ADMIN_HDR, json=payload, timeout=20)
    print('POST Status:', r.status_code)
    if r.ok:
        ep_id = r.json().get('id')
        print('POST Success, ep_id:', ep_id)
        if ep_id and sub_url:
            sub_payload = {
                'url': sub_url,
                'language': 'id',
                'label': 'Indonesia'
            }
            r2 = requests.post(f'{API_BASE}/episodes/{ep_id}/subtitles', headers=ADMIN_HDR, json=sub_payload, timeout=10)
            if r2.ok:
                print('SUB Success!')
            else:
                print('SUB Failed:', r2.status_code, r2.text)
    else:
        print('POST Failed:', r.status_code, r.text)
