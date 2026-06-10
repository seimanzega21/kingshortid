import requests
import re

API_BASE = 'https://api.shortlovers.id/api'

def clean_title(t):
    t = t.lower()
    t = re.sub(r'\[versi dub\]|\(sulih suara\)|\[dubbing\]|\[dijuluki\]', '', t)
    return re.sub(r'[^a-z0-9]', '', t)

r = requests.get(f'{API_BASE}/dramas?limit=1000')
if r.ok:
    dramas = r.json().get('dramas', [])
    print(f'Total active dramas fetched: {len(dramas)}')
    
    seen = {}
    for d in dramas:
        c = clean_title(d['title'])
        if c in seen:
            seen[c].append(d)
        else:
            seen[c] = [d]
            
    print('\nACTIVE DUPLICATES:')
    for c, arr in seen.items():
        if len(arr) > 1:
            print(f'DUPLICATE: {arr[0]["title"]}')
            for d in arr:
                print(f"  - ID: {d['id']}, Title: {d['title']}, Cover: {d['cover']}, Active: {d.get('isActive', True)}")
