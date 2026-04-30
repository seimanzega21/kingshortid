import requests
import time

ADMIN_KEY='00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
API_BASE='https://api.shortlovers.id'
HEADERS={'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

def main():
    # 1. Get all dramas
    print("Fetching dramas...")
    res = requests.get(f'{API_BASE}/api/dramas?limit=2000&includeInactive=true', headers=HEADERS).json()
    dramas = res.get('dramas', [])
    
    # 2. Filter active dramas
    active_dramas = [d for d in dramas if d['isActive']]
    print(f"Found {len(active_dramas)} active dramas.")
    
    for d in active_dramas:
        d_id = d['id']
        print(f"Checking episodes for: {d['title']} ({d_id})")
        
        # Get all episodes (including inactive)
        detail = requests.get(f'{API_BASE}/api/dramas/{d_id}?includeInactive=true', headers=HEADERS).json()
        episodes = detail.get('episodes', [])
        
        inactive_eps = [e for e in episodes if not e['isActive']]
        if not inactive_eps:
            print("  All episodes already active.")
            continue
            
        print(f"  Activating {len(inactive_eps)} episodes...")
        for ep in inactive_eps:
            ep_id = ep['id']
            patch_res = requests.patch(f'{API_BASE}/api/episodes/{ep_id}', 
                                      headers=HEADERS, 
                                      json={'isActive': True})
            if not patch_res.ok:
                print(f"    Failed to activate ep {ep['episodeNumber']}: {patch_res.status_code}")
                if patch_res.status_code == 429:
                    print("    Rate limited. Waiting 5s...")
                    time.sleep(5)
            else:
                time.sleep(1) # Slow down to avoid rate limit
            
    print("Done!")

if __name__ == "__main__":
    main()
