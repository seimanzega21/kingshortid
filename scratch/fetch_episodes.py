import sys
import requests
import json

admin_key = None
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
ADMIN_HDR = {'x-admin-key': admin_key}

r = requests.get(f'{API_BASE}/admin/dramas', headers=ADMIN_HDR)
if r.ok:
    dramas = r.json().get('dramas', [])
    dewa = next((d for d in dramas if d['id'] == 'dt9wnyumb4fj2i51p6r9kwds'), None)
    if dewa:
        print('Found Dewa:', dewa['title'])
        r2 = requests.get(f'{API_BASE}/admin/dramas/dt9wnyumb4fj2i51p6r9kwds/episodes', headers=ADMIN_HDR)
        if r2.ok:
            ep33 = next((e for e in r2.json() if e['episodeNumber'] == 33), None)
            print('Ep 33:', json.dumps(ep33, indent=2))
        else:
            print('Failed to get episodes:', r2.status_code, r2.text)
    else:
        print('Dewa not found in admin list')
else:
    print('Failed admin list:', r.status_code)
