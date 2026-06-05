import requests
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

API_BASE    = 'https://api.shortlovers.id/api'
ADMIN_KEY   = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR   = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

title = "Permainan Terlarang Mereka"

print(f"Searching database for '{title}'...")
r = requests.get(f"{API_BASE}/dramas?search={title}&includeInactive=true", timeout=10)
if r.ok:
    dramas = r.json()
    if isinstance(dramas, dict):
        dramas = dramas.get('dramas', dramas.get('data', []))
    
    if not dramas:
        print("Drama not found in database!")
    else:
        d = dramas[0]
        print(f"FOUND: '{d['title']}' (ID: {d['id']}, Active: {d.get('isActive')})")
        
        # Get episodes details
        r_eps = requests.get(f"{API_BASE}/dramas/{d['id']}?includeInactive=true", timeout=10)
        if r_eps.ok:
            d_detail = r_eps.json()
            episodes = d_detail.get('episodes', [])
            print(f"Total episodes registered in DB: {len(episodes)}")
            
            # Print subtitle details
            print("\nRegistered Subtitles per Episode:")
            for ep in sorted(episodes, key=lambda e: e.get('episodeNumber', 0)):
                ep_num = ep.get('episodeNumber')
                # Let's check subtitles for this episode.
                # In the DB structure, subtitles are usually nested inside ep as 'subtitles' list
                subs = ep.get('subtitles', [])
                sub_info = ", ".join([f"{s.get('language')}: {s.get('url')}" for s in subs]) if subs else "NONE"
                print(f"  - Episode {ep_num}: {sub_info}")
        else:
            print(f"Error fetching episodes details: {r_eps.status_code}")
else:
    print(f"Error searching database: {r.status_code}")
