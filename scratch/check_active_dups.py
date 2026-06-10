import requests
import json
import re

API_BASE = 'https://api.shortlovers.id/api'

def clean_title(t):
    t = t.lower()
    t = re.sub(r'\[versi dub\]|\(sulih suara\)|\[dubbing\]|\[dijuluki\]', '', t)
    return re.sub(r'[^a-z0-9]', '', t)

r = requests.get(f'{API_BASE}/dramas')
if r.ok:
    dramas = r.json()
    dramas = dramas if isinstance(dramas, list) else dramas.get('dramas', [])
    seen = {}
    for d in dramas:
        c = clean_title(d['title'])
        if c in seen:
            seen[c].append(d)
        else:
            seen[c] = [d]
            
    for c, arr in seen.items():
        if len(arr) > 1:
            print(f'DUPLICATE: {arr[0]["title"]}')
            for d in arr:
                print(f"  - ID: {d['id']}, Title: {d['title']}, Cover: {d['cover']}")
