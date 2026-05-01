# -*- coding: utf-8 -*-
import requests, sys

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

API_BASE = 'https://api.shortlovers.id'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

# Search for drama by title
r = requests.get(f"{API_BASE}/api/dramas", headers=ADMIN_HDR, timeout=20)
if r.ok:
    result = r.json()
    dramas = result.get('dramas', []) if isinstance(result, dict) else result
    for d in dramas:
        title = d.get('title', '').lower()
        if 'pewaris' in title or 'perjuangan' in title:
            print(f"DB DRAMA FOUND: {d.get('title')} | ID: {d.get('id')} | isActive: {d.get('isActive')} | Episodes: {d.get('totalEpisodes')}")
            # Get episodes
            ep_r = requests.get(f"{API_BASE}/api/dramas/{d.get('id')}/episodes", headers=ADMIN_HDR, timeout=20)
            if ep_r.ok:
                ep_result = ep_r.json()
                eps = ep_result.get('episodes', []) if isinstance(ep_result, dict) else ep_result
                print(f"  Episodes in DB: {len(eps)}")
                if eps:
                    print(f"  First: ep{eps[0].get('episodeNumber')}, Last: ep{eps[-1].get('episodeNumber')}")
                    # Count episodes with video
                    with_video = sum(1 for ep in eps if ep.get('videoUrl'))
                    print(f"  With videoUrl: {with_video}")
            else:
                print(f"  Failed to get episodes: {ep_r.status_code} | {ep_r.text[:200]}")
else:
    print(f"Failed to get dramas: {r.status_code} | {r.text[:200]}")
