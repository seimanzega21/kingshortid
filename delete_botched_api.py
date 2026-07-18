import requests

API_BASE = 'http://localhost:3000/api'
ADMIN_HDR = {'x-admin-key': '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'}
r = requests.delete(f"{API_BASE}/admin/dramas/v7j8h3x5evzvxxh5lnqcmv4r", headers=ADMIN_HDR)
print("Status Code:", r.status_code)
print("Response:", r.text)
