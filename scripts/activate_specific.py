import requests
import time

ADMIN_KEY='00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
API_BASE='https://api.shortlovers.id'
HEADERS={'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}
DRAMA_ID='l71e0zm1tcrwin4j6zeyb0l6'

def main():
    print(f"Fetching drama {DRAMA_ID}...")
    res = requests.get(f'{API_BASE}/api/dramas/{DRAMA_ID}?includeInactive=true', headers=HEADERS).json()
    eps = res.get('episodes', [])
    
    inactive = [e for e in eps if not e['isActive']]
    print(f"Activating {len(inactive)} episodes...")
    
    for ep in inactive:
        r = requests.patch(f"{API_BASE}/api/episodes/{ep['id']}", headers=HEADERS, json={'isActive': True})
        print(f"  Ep {ep['episodeNumber']}: {r.status_code}")
        if r.status_code == 429:
            print("  Rate limited! Sleeping 5s...")
            time.sleep(5)
        else:
            time.sleep(0.5)

if __name__ == "__main__":
    main()
