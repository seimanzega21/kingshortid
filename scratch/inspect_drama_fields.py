import requests

API_BASE = 'https://api.shortlovers.id/api'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY}

r = requests.get(f"{API_BASE}/dramas?limit=5&includeInactive=true", headers=ADMIN_HDR)
if r.ok:
    dramas = r.json()
    if isinstance(dramas, dict):
        dramas = dramas.get('dramas', [])
    if dramas:
        print("Keys in drama:")
        print(dramas[0].keys())
        print("\nProviders present in sample:")
        providers = {d.get("provider") for d in dramas}
        print(providers)
        print("\nFirst drama full data:")
        print(dramas[0])
