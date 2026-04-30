import requests

ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
API_BASE = 'https://api.shortlovers.id'
DRAMA_ID = 'qr6s1vtsgh7cf17fqtobp1qt'

def main():
    # 1. Activate Drama
    print(f"Activating drama {DRAMA_ID}...")
    res = requests.patch(
        f"{API_BASE}/api/admin/dramas/{DRAMA_ID}", 
        headers={'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'},
        json={'isActive': True},
        timeout=10
    )
    print(f"  Result: {res.status_code}")

    # 2. Activate Episodes
    print(f"Fetching episodes...")
    url = f"{API_BASE}/api/dramas/{DRAMA_ID}?includeInactive=true"
    r = requests.get(url, headers={'x-admin-key': ADMIN_KEY}, timeout=15)
    if r.status_code != 200:
        print(f"Failed to fetch drama: {r.status_code}")
        return
    
    eps = r.json().get('episodes', [])
    print(f"Found {len(eps)} episodes total.")
    
    count = 0
    for ep in eps:
        if not ep.get('isActive'):
            res = requests.patch(
                f"{API_BASE}/api/episodes/{ep['id']}", 
                headers={'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'},
                json={'isActive': True},
                timeout=10
            )
            if res.status_code == 200:
                print(f"  Ep {ep.get('episodeNumber')}: ACTIVATED")
                count += 1
            else:
                print(f"  Ep {ep.get('episodeNumber')}: FAILED ({res.status_code})")
                
    print(f"\nDone! Activated {count} episodes for Wanita Jenius.")

if __name__ == "__main__":
    main()
