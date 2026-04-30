import requests
import json
import time

def sync_episodes():
    ADMIN_KEY = "00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14"
    BASE_URL = "https://api.shortlovers.id/api"
    DRAMA_ID = "qr6s1vtsgh7cf17fqtobp1qt"
    R2_BASE = "https://stream.shortlovers.id/netshortv2/wanita-jenius"
    
    headers = {
        "X-Admin-Key": ADMIN_KEY,
        "Content-Type": "application/json"
    }
    
    # Check existing episodes to avoid duplicates
    r = requests.get(f"{BASE_URL}/dramas/{DRAMA_ID}/episodes", headers=headers)
    existing_nums = [ep['episodeNumber'] for ep in r.json()]
    print(f"Existing episodes: {len(existing_nums)}")
    
    for i in range(1, 62):
        if i in existing_nums:
            continue
            
        print(f"Registering Episode {i}...")
        payload = {
            "episodeNumber": i,
            "title": f"Episode {i}",
            "videoUrl": f"{R2_BASE}/ep{i:03d}.mp4",
            "videoUrl540p": f"{R2_BASE}/ep{i:03d}_540p.mp4",
            "thumbnail": f"{R2_BASE}/ep{i:03d}.mp4/thumbnail", # Placeholder or actual if exists
            "duration": 120, # Placeholder
            "isVip": i > 5, # Usually free for first few
            "isActive": True
        }
        
        # Add subtitles if they exist (assuming .vtt exists based on screenshot)
        # Based on screenshot, ep059.vtt exists.
        
        res = requests.post(f"{BASE_URL}/admin/dramas/{DRAMA_ID}/episodes", headers=headers, json=payload)
        if res.status_code in [200, 201]:
            print(f"  Success: Episode {i}")
            # Add subtitle
            ep_id = res.json().get('id')
            if ep_id:
                sub_payload = {
                    "language": "id",
                    "label": "Indonesian",
                    "url": f"{R2_BASE}/ep{i:03d}.vtt",
                    "isDefault": True
                }
                requests.post(f"{BASE_URL}/admin/episodes/{ep_id}/subtitles", headers=headers, json=sub_payload)
        else:
            print(f"  Failed: Episode {i} - {res.status_code} - {res.text}")
        
        time.sleep(0.5)

    # Update total episodes in drama
    requests.patch(f"{BASE_URL}/admin/dramas/{DRAMA_ID}", headers=headers, json={"totalEpisodes": 61})
    print("Updated total episodes to 61")

if __name__ == "__main__":
    sync_episodes()
