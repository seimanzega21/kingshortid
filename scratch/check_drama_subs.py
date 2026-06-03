import requests
import json

API_BASE = "https://api.shortlovers.id/api"
ADMIN_KEY = "00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14"
ADMIN_HDR = {"x-admin-key": ADMIN_KEY, "Content-Type": "application/json"}

def check():
    title = "Mendengar Isi Hatimu"
    print(f"Searching for drama: '{title}'")
    
    # 1. Search for drama
    r = requests.get(f"{API_BASE}/dramas?search={title}&includeInactive=true", headers=ADMIN_HDR)
    if not r.ok:
        print("Search failed:", r.status_code, r.text)
        return
        
    dramas = r.json()
    if isinstance(dramas, dict):
        dramas = dramas.get("dramas", [])
        
    print(f"Search returned {len(dramas)} dramas:")
    for idx, d in enumerate(dramas):
        print(f"  [{idx}] {d['title']} (ID: {d['id']})")
        
    if not dramas:
        print("Drama not found!")
        return
        
    # Find matching title
    drama = next((d for d in dramas if "Mendengar" in d["title"]), dramas[0])
    drama_id = drama["id"]
    print(f"Selected drama: {drama['title']} (ID: {drama_id})")
    print(json.dumps(drama, indent=2))
    
    # 2. Get drama details (including episodes)
    r = requests.get(f"{API_BASE}/dramas/{drama_id}?includeInactive=true", headers=ADMIN_HDR)
    if not r.ok:
        print("Get drama details failed:", r.status_code, r.text)
        return
        
    details = r.json()
    eps = details.get("episodes", [])
    print(f"Drama total episodes: {details.get('totalEpisodes')} | Episodes in details: {len(eps)}")
    
    # Find target episodes
    target_eps = [1, 10, 20, 30, 31, 40]
    for ep_num in target_eps:
        ep = next((e for e in eps if e.get("episodeNumber") == ep_num), None)
        if not ep:
            print(f"Episode {ep_num} not found in episode list!")
            continue
            
        ep_id = ep["id"]
        print(f"\n--- Episode {ep_num} (ID: {ep_id}) ---")
        print(f"  Title: {ep.get('title')}")
        print(f"  videoUrl: {ep.get('videoUrl')}")
        print(f"  videoUrl540p: {ep.get('videoUrl540p')}")
        
        # Check subtitles via API
        r_ep = requests.get(f"{API_BASE}/episodes/{ep_id}/subtitles", headers=ADMIN_HDR)
        if r_ep.ok:
            subs = r_ep.json().get("subtitles", [])
            print(f"  Subtitles from GET /episodes/{{id}}/subtitles: {subs}")
        else:
            print(f"  Failed to get subtitles: {r_ep.status_code} {r_ep.text}")
            
if __name__ == "__main__":
    check()
