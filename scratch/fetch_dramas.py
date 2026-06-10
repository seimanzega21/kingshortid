import requests
import json
import re

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

def clean_title(t):
    t = t.lower()
    t = re.sub(r'\[versi dub\]', '', t)
    t = re.sub(r'\(sulih suara\)', '', t)
    t = re.sub(r'\[dubbing\]', '', t)
    t = re.sub(r'[^a-z0-9]', '', t)
    return t

r = requests.get(f'{API_BASE}/admin/dramas', headers=ADMIN_HDR)
if r.ok:
    data = r.json()
    dramas = data.get('dramas', []) if isinstance(data, dict) else data
    if isinstance(dramas, dict):
        dramas = dramas.get('data', []) # sometimes paginated?
    
    print(f'Total admin dramas: {len(dramas)}')
    for d in dramas[:5]:
        print('-', d.get('title'))
        
    # Check what endpoint returns
else:
    print('Admin list failed:', r.status_code, r.text)

r2 = requests.get(f'{API_BASE}/dramas')
if r2.ok:
    data2 = r2.json()
    dramas2 = data2 if isinstance(data2, list) else data2.get('dramas', [])
    print(f'Total public dramas: {len(dramas2)}')
