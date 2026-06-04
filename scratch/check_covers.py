import requests
import json
from pathlib import Path

API_BASE = 'https://api.shortlovers.id/api'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
headers = {'x-admin-key': ADMIN_KEY}

with open('scratch/mapped_netshortv2_dramas.json', 'r') as f:
    mapped = json.load(f)

for item in mapped:
    db_id = item['db_id']
    r = requests.get(f'{API_BASE}/dramas/{db_id}?includeInactive=true', headers=headers)
    if r.ok:
        data = r.json()
        print(f"{data.get('title')}: {data.get('cover')}")
    else:
        print(f"Failed to fetch {item['title']}: {r.status_code}")
