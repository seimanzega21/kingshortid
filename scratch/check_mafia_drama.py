import requests
import json

API_BASE = 'https://api.shortlovers.id/api'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
headers = {'x-admin-key': ADMIN_KEY}

db_id = 'xmewhikaocggtjkchduc2qc0'

# 1. Fetch drama detail
r = requests.get(f"{API_BASE}/dramas/{db_id}?includeInactive=true", headers=headers)
if r.ok:
    drama = r.json()
    print("DRAMA DETAIL:")
    print(json.dumps(drama, indent=2))
else:
    print(f"Failed to fetch drama detail: {r.status_code}")
    exit(1)

# 2. Fetch episodes
r_eps = requests.get(f"{API_BASE}/dramas/{db_id}/episodes?includeInactive=true", headers=headers)
if r_eps.ok:
    eps = r_eps.json()
    ep_list = eps if isinstance(eps, list) else eps.get('episodes', eps.get('data', []))
    print(f"\nTotal episodes registered in DB: {len(ep_list)}")
    print("Registered episode numbers:")
    ep_nums = sorted([e.get('episodeNumber') for e in ep_list])
    print(ep_nums)
    
    # Check details of first few episodes to see their URL prefix/pattern
    if ep_list:
        print("\nFirst 3 episodes detail:")
        for e in sorted(ep_list, key=lambda x: x.get('episodeNumber', 0))[:3]:
            print(f"  Ep {e.get('episodeNumber')}: videoUrl={e.get('videoUrl')}")
else:
    print(f"Failed to fetch episodes: {r_eps.status_code}")
