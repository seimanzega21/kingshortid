import requests
import time

headers = {'Authorization': 'Bearer 00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'}
r = requests.get('http://localhost:3000/api/dramas?limit=500&includeInactive=true', headers=headers).json()

v = int(time.time())

for d in r.get('dramas', []):
    if 'Pembawa' in d['title']:
        nc = d['cover'].split('?')[0] + f"?v={v}"
        res = requests.patch(f"http://localhost:3000/api/dramas/{d['id']}", json={'cover': nc, 'coverUrl': nc}, headers=headers)
        print(f"Busted: {d['title']} -> {nc}")
