"""Activate a drama + all its episodes in one shot."""
import requests
import time

ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
API_BASE = 'https://api.shortlovers.id'
HEADERS = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

DRAMA_ID = 'uyeo1d9picfq4qykbj0bzjzn'

def main():
    # 1. Activate the drama itself
    r = requests.patch(f'{API_BASE}/api/admin/dramas/{DRAMA_ID}', headers=HEADERS, json={'isActive': True})
    print(f'Drama activate: {r.status_code}')

    # 2. Fetch all episodes
    res = requests.get(f'{API_BASE}/api/dramas/{DRAMA_ID}?includeInactive=true&_={int(time.time())}', headers=HEADERS).json()
    eps = res.get('episodes', [])
    inactive = [e for e in eps if not e['isActive']]
    print(f'Found {len(eps)} episodes, {len(inactive)} are inactive.')

    # 3. Activate all inactive episodes
    success, fail = 0, 0
    for ep in inactive:
        ep_id = ep['id']
        ep_num = ep['episodeNumber']
        for attempt in range(3):
            try:
                r = requests.patch(f'{API_BASE}/api/episodes/{ep_id}', headers=HEADERS, json={'isActive': True})
                if r.status_code == 200:
                    print(f'  Ep {ep_num}: SUCCESS')
                    success += 1
                    break
                elif r.status_code == 429:
                    print(f'  Ep {ep_num}: Rate limited, waiting...')
                    time.sleep(5)
                else:
                    print(f'  Ep {ep_num}: FAILED ({r.status_code})')
                    fail += 1
                    break
            except Exception as e:
                print(f'  Ep {ep_num}: ERROR {e}')
                fail += 1
                break
        time.sleep(0.3)

    print(f'\nDone! Success: {success}, Failed: {fail}')

if __name__ == '__main__':
    main()
