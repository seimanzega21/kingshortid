import requests
import json

API_BASE = 'https://api.shortlovers.id'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

did = 'tht294kp6q3x79if36ahkyjg'

# Get episodes
r = requests.get(f"{API_BASE}/api/dramas/{did}/episodes?includeInactive=true", headers=ADMIN_HDR, timeout=15)
if r.ok:
    data = r.json()
    episodes = data if isinstance(data, list) else data.get('episodes', data.get('data', []))
    print(f"Total episodes found: {len(episodes)}")
    
    # Sort episodes by episode number
    episodes.sort(key=lambda x: x.get('episodeNumber', 0))
    
    for ep in episodes:
        num = ep.get('episodeNumber')
        if num in [28, 29, 30, 31, 32, 33]:
            print(f"\nEP {num}:")
            print(f"  ID: {ep.get('id')}")
            print(f"  Video 720p: {ep.get('videoUrl')}")
            print(f"  Video 540p: {ep.get('videoUrl540p')}")
            
            # Fetch subtitles for this episode if any
            sub_r = requests.get(f"{API_BASE}/api/episodes/{ep.get('id')}/subtitles", headers=ADMIN_HDR, timeout=10)
            if sub_r.ok:
                subs = sub_r.json()
                print(f"  Subtitles: {json.dumps(subs, indent=2)}")
            else:
                print(f"  Subtitles request failed: {sub_r.status_code}")
else:
    print(f"Error: {r.status_code} {r.text}")
