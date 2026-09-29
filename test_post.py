
import requests
API_BASE = 'https://api.shortlovers.id/api'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

payload = {
    'dramaId': 'y8o6b5ff5tm1n1cq11wy81o7',
    'episodeNumber': 128,
    'title': 'Test Episode'
}
res = requests.post(f'{API_BASE}/episodes', json=payload, headers=ADMIN_HDR)
print(res.status_code)
print(res.text)

