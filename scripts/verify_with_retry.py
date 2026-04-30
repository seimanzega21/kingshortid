import requests
import time

ADMIN_KEY='00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
API_BASE='https://api.shortlovers.id'
DRAMA_ID='l71e0zm1tcrwin4j6zeyb0l6'

def get_with_retry(url, headers=None):
    while True:
        r = requests.get(url, headers=headers)
        if r.status_code == 429:
            retry_after = int(r.json().get('retryAfter', 5))
            print(f"Rate limited. Waiting {retry_after}s...")
            time.sleep(retry_after + 1)
            continue
        return r

def main():
    print(f"Checking drama {DRAMA_ID}...")
    # Public check (no admin key)
    r = get_with_retry(f'{API_BASE}/api/dramas/{DRAMA_ID}')
    if r.ok:
        data = r.json()
        eps = data.get('episodes', [])
        print(f"Public API: Total={data.get('totalEpisodes')}, Count={len(eps)}")
        print(f"Active Episodes in Response: {[e['episodeNumber'] for e in eps]}")
    else:
        print(f"Public API Error: {r.status_code} {r.text}")

    # Admin check
    r_admin = get_with_retry(f'{API_BASE}/api/dramas/{DRAMA_ID}?includeInactive=true', 
                             headers={'x-admin-key': ADMIN_KEY})
    if r_admin.ok:
        data = r_admin.json()
        eps = data.get('episodes', [])
        active = [e for e in eps if e['isActive']]
        print(f"Admin API: Total={len(eps)}, Active={len(active)}")
    else:
        print(f"Admin API Error: {r_admin.status_code} {r_admin.text}")

if __name__ == "__main__":
    main()
