import requests
import json

API_BASE = 'https://api.shortlovers.id/api'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
headers = {'x-admin-key': ADMIN_KEY}

# 1. Search for the drama
r = requests.get(f"{API_BASE}/dramas/search?q=Mencari Sinar di Lautan", headers=headers)
if r.ok:
    print("Search response:", r.json())
else:
    print(f"Search failed: {r.status_code}")

r_all = requests.get(f"{API_BASE}/dramas?limit=1500&includeInactive=true", headers=headers)
dlist = r_all.json()
if isinstance(dlist, dict):
    dlist = dlist.get('dramas', [])
dramas = [d for d in dlist if 'sinar' in d.get('title', '').lower()]
print("Dramas found via list search:", dramas)


for d in dramas:
    print("=" * 60)
    print(f"DRAMA: {d.get('title')} (ID: {d.get('id')})")
    print(f"Cover: {d.get('cover')}")
    print(f"Is Active: {d.get('isActive')}")
    print("=" * 60)
    
    # Get episodes
    ep_r = requests.get(f"{API_BASE}/dramas/{d.get('id')}/episodes?includeInactive=true", headers=headers)
    if not ep_r.ok:
        print(f"Failed to get episodes: {ep_r.status_code}")
        continue
        
    eps = ep_r.json()
    ep_list = eps if isinstance(eps, list) else eps.get('episodes', eps.get('data', []))
    print(f"Total episodes registered: {len(ep_list)}")
    
    if not ep_list:
        continue
        
    # Check first 3 episodes
    for ep in sorted(ep_list, key=lambda x: x.get('episodeNumber', 0))[:3]:
        ep_id = ep.get('id')
        ep_no = ep.get('episodeNumber')
        print(f"\n  Episode {ep_no} (ID: {ep_id}):")
        print(f"    Title: {ep.get('title')}")
        print(f"    Video URL: {ep.get('videoUrl')}")
        print(f"    Video URL 540p: {ep.get('videoUrl540p')}")
        
        # Get subtitles for this episode
        sub_r = requests.get(f"{API_BASE}/episodes/{ep_id}/subtitles", headers=headers)
        if sub_r.ok:
            subs = sub_r.json()
            sub_list = subs if isinstance(subs, list) else subs.get('subtitles', subs.get('data', []))
            print(f"    Subtitles count: {len(sub_list)}")
            for s in sub_list:
                print(f"      - Lang: {s.get('language')}, Label: {s.get('label')}, URL: {s.get('url')}, IsDefault: {s.get('isDefault')}")
        else:
            print(f"    Failed to get subtitles: {sub_r.status_code}")
