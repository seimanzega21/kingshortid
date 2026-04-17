import requests
import time

headers = {'Authorization': 'Bearer 00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'}
r = requests.get('http://localhost:3000/api/dramas?limit=500&includeInactive=true', headers=headers).json()

count = 0
v = int(time.time())

for d in r.get('dramas', []):
    if d.get('cover') and 'netshort' in d['cover']:
        nc = d['cover'].split('?')[0] + f"?v={v}"
        
        # We also need to patch coverUrl if the DB contains it (although only cover is shown in API)
        payload = {'cover': nc}
        
        res = requests.patch(f"http://localhost:3000/api/dramas/{d['id']}", json=payload, headers=headers)
        if res.status_code == 200:
            count += 1
            print(f"Busted: {d['title']}")
        else:
            print(f"Failed: {d['title']} -> {res.status_code}")

print(f"Total busted: {count}")
