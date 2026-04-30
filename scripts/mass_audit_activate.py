"""
Mass Audit & Activate Script
Cari semua drama yang isActive=True tapi episodenya masih inactive,
lalu aktifkan semua episodenya sekaligus.
"""
import requests
import time

ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
API_BASE = 'https://api.shortlovers.id'
HEADERS = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

def get_all_dramas():
    """Ambil semua drama (active + inactive) dari admin."""
    all_dramas = []
    page = 1
    while True:
        res = requests.get(f'{API_BASE}/api/dramas?page={page}&limit=100&includeInactive=true', headers=HEADERS).json()
        dramas = res.get('dramas', [])
        if not dramas:
            break
        all_dramas.extend(dramas)
        print(f'  Fetched page {page}: {len(dramas)} dramas (total so far: {len(all_dramas)})')
        if len(dramas) < 100:
            break
        page += 1
        time.sleep(0.5)
    return all_dramas

def activate_drama_episodes(drama_id, drama_title):
    """Aktifkan semua episode yang masih inactive untuk satu drama."""
    res = requests.get(
        f'{API_BASE}/api/dramas/{drama_id}?includeInactive=true&_={int(time.time())}',
        headers=HEADERS
    ).json()
    eps = res.get('episodes', [])
    inactive = [e for e in eps if not e.get('isActive', True)]
    
    if not inactive:
        return 0, 0
    
    print(f'  >> [{drama_title[:50]}] {len(inactive)}/{len(eps)} inactive eps -> activating...')
    
    success, fail = 0, 0
    for ep in inactive:
        ep_id = ep['id']
        for attempt in range(3):
            try:
                r = requests.patch(f'{API_BASE}/api/episodes/{ep_id}', headers=HEADERS, json={'isActive': True})
                if r.status_code == 200:
                    success += 1
                    break
                elif r.status_code == 429:
                    time.sleep(5)
                else:
                    fail += 1
                    break
            except Exception as e:
                fail += 1
                break
        time.sleep(0.2)
    
    return success, fail

def main():
    print('=== MASS AUDIT & ACTIVATE ===\n')
    
    # 1. Fetch semua drama
    print('Step 1: Fetching all dramas...')
    all_dramas = get_all_dramas()
    print(f'Total dramas found: {len(all_dramas)}\n')
    
    # 2. Filter hanya yang isActive=True
    active_dramas = [d for d in all_dramas if d.get('isActive')]
    inactive_dramas = [d for d in all_dramas if not d.get('isActive')]
    print(f'Active dramas: {len(active_dramas)}')
    print(f'Inactive dramas (skipped): {len(inactive_dramas)}\n')
    
    # 3. Cek dan aktifkan episode untuk setiap drama aktif
    print('Step 2: Checking & activating episodes for active dramas...')
    total_activated = 0
    dramas_fixed = 0
    
    for i, drama in enumerate(active_dramas):
        drama_id = drama['id']
        drama_title = drama.get('title', 'Unknown')
        
        activated, failed = activate_drama_episodes(drama_id, drama_title)
        if activated > 0:
            total_activated += activated
            dramas_fixed += 1
            print(f'    OK {activated} episodes activated')
        
        # Progress update setiap 10 drama
        if (i + 1) % 10 == 0:
            print(f'\n  Progress: {i+1}/{len(active_dramas)} dramas checked...\n')
        
        time.sleep(0.3)
    
    print(f'\n=== DONE ===')
    print(f'Dramas with episodes fixed: {dramas_fixed}')
    print(f'Total episodes activated: {total_activated}')

if __name__ == '__main__':
    main()
