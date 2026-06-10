import sys
import requests
import json

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
ADMIN_HDR = {'x-admin-key': admin_key}

r = requests.get(f'{API_BASE}/admin/dramas/dt9wnyumb4fj2i51p6r9kwds', headers=ADMIN_HDR)
if r.ok:
    data = r.json()
    ep33 = next((e for e in data.get('episodes', []) if e['episodeNumber'] == 33), None)
    if ep33:
        print(json.dumps(ep33, indent=2))
    else:
        print('Ep 33 not found in API')
else:
    print('Failed:', r.status_code, r.text)
