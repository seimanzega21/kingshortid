import requests

API_BASE = 'https://api.shortlovers.id'
DRAMA_ID = 'pjr00rw58d0y73bk7axn1buy'

print("=== VERIFYING JANJI KUNO EPISODES ===")
url = f"{API_BASE}/api/dramas/{DRAMA_ID}/episodes?includeInactive=true"
r = requests.get(url, timeout=15)
if r.ok:
    eps = r.json()
    ep_list = eps if isinstance(eps, list) else eps.get('episodes', eps.get('data', []))
    print(f"Total episodes in database: {len(ep_list)}")
    
    # Sort
    ep_list.sort(key=lambda x: x.get('episodeNumber', 0))
    
    # Print status of episodes 24 to 37
    for e in ep_list:
        num = e.get('episodeNumber')
        if 24 <= num <= 37:
            print(f"EP {num:02d}: ID={e.get('id')} | 720p={e.get('videoUrl')} | 540p={e.get('videoUrl540p')}")
else:
    print("Verification failed:", r.status_code)
