import requests
import re

API_BASE = 'https://api.shortlovers.id/api'
headers = {'x-admin-key': 'ksh-admin-2026-s3cur3-k3y-x7m9p2'}

def clean_title(t):
    t = t.lower()
    t = re.sub(r'\[versi dub\]|\(sulih suara\)|\[dubbing\]|\[dijuluki\]', '', t)
    return re.sub(r'[^a-z0-9]', '', t)

# Fetch all dramas from admin API
r = requests.get(f'{API_BASE}/admin/dramas?limit=5000', headers=headers)
if r.ok:
    dramas = r.json().get('dramas', [])
    print(f'Total dramas fetched: {len(dramas)}')
    
    seen = {}
    for d in dramas:
        c = clean_title(d['title'])
        if c in seen:
            seen[c].append(d)
        else:
            seen[c] = [d]
            
    print('\nDUPLICATES FOUND:')
    for c, arr in seen.items():
        if len(arr) > 1:
            print(f'DUPLICATE: {arr[0]["title"]}')
            for d in arr:
                status = "ACTIVE" if d.get('isActive') else "PENDING"
                print(f"  - ID: {d['id']}, Title: {d['title']}, Status: {status}, Cover: {d['cover']}")
else:
    print(f"Failed to fetch admin API: {r.status_code}")
