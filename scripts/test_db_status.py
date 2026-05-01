import requests

API_BASE = 'https://api.shortlovers.id'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

# Search for drama by title
print('=== CHECK KINGSHORT DATABASE ===')
r = requests.get(f"{API_BASE}/api/dramas", headers=ADMIN_HDR, timeout=20)
if r.ok:
    dramas = r.json().get('dramas', [])
    for d in dramas:
        title = d.get('title', '').lower()
        if 'pewaris' in title or 'perjuangan' in title:
            print(f"DB DRAMA: {d.get('title')} | ID: {d.get('id')} | isActive: {d.get('isActive')} | totalEpisodes: {d.get('totalEpisodes')}")
            # Get episodes
            ep_r = requests.get(f"{API_BASE}/api/dramas/{d.get('id')}/episodes", headers=ADMIN_HDR, timeout=20)
            if ep_r.ok:
                data = ep_r.json()
                # Response might be list or object
                if isinstance(data, list):
                    eps = data
                else:
                    eps = data.get('episodes', [])
                print(f"  Episodes in DB: {len(eps)}")
                if eps:
                    ep_nums = [ep.get('episodeNumber') for ep in eps]
                    print(f"  Episode numbers: {ep_nums}")
                    # Count episodes with video
                    with_video = sum(1 for ep in eps if ep.get('videoUrl'))
                    print(f"  With videoUrl: {with_video}")
                    without_video = [ep.get('episodeNumber') for ep in eps if not ep.get('videoUrl')]
                    if without_video:
                        print(f"  WITHOUT videoUrl: {without_video}")
            else:
                print(f"  Failed to get episodes: {ep_r.status_code}")
else:
    print(f"Failed to get dramas: {r.status_code} {r.text[:200]}")

# Also check if drama exists by direct ID (the one from previous work)
print()
print('=== CHECK BY DIRECT ID (r63qbi2gnxtjvpsaigqpybl0) ===')
drama_id = 'r63qbi2gnxtjvpsaigqpybl0'
dr_r = requests.get(f"{API_BASE}/api/dramas/{drama_id}", headers=ADMIN_HDR, timeout=20)
print(f"Status: {dr_r.status_code}")
if dr_r.ok:
    drama = dr_r.json()
    print(f"Title: {drama.get('title')}")
    print(f"isActive: {drama.get('isActive')}")
    print(f"totalEpisodes: {drama.get('totalEpisodes')}")
    
    ep_r = requests.get(f"{API_BASE}/api/dramas/{drama_id}/episodes", headers=ADMIN_HDR, timeout=20)
    if ep_r.ok:
        data = ep_r.json()
        eps = data if isinstance(data, list) else data.get('episodes', [])
        print(f"Episodes in DB: {len(eps)}")
        if eps:
            ep_nums = [ep.get('episodeNumber') for ep in eps]
            print(f"Episode numbers: {ep_nums}")
            with_video = sum(1 for ep in eps if ep.get('videoUrl'))
            print(f"With videoUrl: {with_video}")
            without_video = [ep.get('episodeNumber') for ep in eps if not ep.get('videoUrl')]
            if without_video:
                print(f"WITHOUT videoUrl: {without_video}")
