import requests
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

API_BASE = 'https://api.shortlovers.id'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

def check_drama_eps(did):
    # Fetch drama info
    r = requests.get(f"{API_BASE}/api/dramas/{did}", headers=ADMIN_HDR, timeout=15)
    if r.ok:
        d = r.json()
        print(f"DRAMA: {d.get('title')} (ID: {d.get('id')})")
        print(f"Description: {d.get('description')}")
        print(f"Total Episodes: {d.get('totalEpisodes')}")
    else:
        print(f"Failed to get drama info: {r.status_code} {r.text}")
        return

    # Fetch episodes
    r = requests.get(f"{API_BASE}/api/dramas/{did}/episodes", headers=ADMIN_HDR, timeout=15)
    if r.ok:
        res = r.json()
        eps = res.get('episodes', []) if isinstance(res, dict) else res
        print(f"Total episodes in DB: {len(eps)}")
        
        # Check first 5 episodes
        for i, ep in enumerate(eps[:5]):
            print(f"\nEpisode {ep.get('episodeNumber')}:")
            print(f"  ID: {ep.get('id')}")
            print(f"  Title: {ep.get('title')}")
            print(f"  Video URL: {ep.get('videoUrl')}")
            print(f"  Subtitle URL: {ep.get('subtitleUrl')}")
            print(f"  Is Free: {ep.get('isFree')}")
            
        # Analyze resolutions in all episodes
        all_urls = [ep.get('videoUrl') for ep in eps if ep.get('videoUrl')]
        print(f"\nAnalysis of {len(all_urls)} video URLs:")
        mp4_count = sum(1 for u in all_urls if u.lower().endswith('.mp4'))
        m3u8_count = sum(1 for u in all_urls if '.m3u8' in u.lower())
        v540_count = sum(1 for u in all_urls if '_540p' in u.lower())
        v720_count = sum(1 for u in all_urls if '_720p' in u.lower())
        
        print(f"  Ending in .mp4: {mp4_count}")
        print(f"  Contains .m3u8: {m3u8_count}")
        print(f"  Contains '_540p': {v540_count}")
        print(f"  Contains '_720p': {v720_count}")
        
        # Show sample URLs
        if all_urls:
            print("\nSample Video URLs:")
            for u in all_urls[:3]:
                print(f"  {u}")
    else:
        print(f"Failed to get episodes: {r.status_code} {r.text}")

if __name__ == '__main__':
    check_drama_eps('cmlistfgr8006gtlqebrmv3cwm')
