# -*- coding: utf-8 -*-
import requests, json, urllib3, sys
urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

API_BASE = 'https://api.shortlovers.id'
r = requests.get(f"{API_BASE}/api/dramas", timeout=15)
if r.ok:
    dramas = r.json()
    dlist = dramas if isinstance(dramas, list) else dramas.get('dramas', [])
    print(f"Total dramas in KingShort DB: {len(dlist)}")
    for i, d in enumerate(dlist):
        print(f"  {i+1}: ID={d.get('id')} | Title={d.get('title')} | Status={d.get('status')} | Active={d.get('isActive')}")
else:
    print(f"Error: {r.status_code}")
