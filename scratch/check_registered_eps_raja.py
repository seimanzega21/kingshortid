import requests
import json

API_BASE = 'https://api.shortlovers.id/api'
DRAMA_ID = 'n2edv3mw0hw1i60k0ox4y7e3'

url = f"{API_BASE}/dramas/{DRAMA_ID}/episodes?includeInactive=true"
r = requests.get(url, timeout=15)
if r.ok:
    eps = r.json()
    ep_list = eps if isinstance(eps, list) else eps.get('episodes', eps.get('data', []))
    print(f"Total episodes in database for Raja Tanpa Mahkota: {len(ep_list)}")
    
    # Check which episodes exist
    ep_nums = sorted([e.get('episodeNumber') for e in ep_list])
    print("Database episode numbers:", ep_nums)
    
    # Find missing numbers from 1 to 76
    missing = [i for i in range(1, 77) if i not in ep_nums]
    print("Missing episode numbers in database:", missing)
else:
    print("Failed to fetch database episodes:", r.status_code)
