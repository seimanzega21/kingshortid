import requests
import json

API_BASE = 'https://api.shortlovers.id/api'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

DRAMA_ID = 'pjr00rw58d0y73bk7axn1buy'

# Patch request to update totalEpisodes to 72
url = f"{API_BASE}/admin/dramas/{DRAMA_ID}"
payload = {
    'totalEpisodes': 72,
    'status': 'completed' # completed status
}

print(f"Sending PATCH request to {url}...")
r = requests.patch(url, headers=ADMIN_HDR, json=payload, timeout=10)
if r.ok:
    print("SUCCESS! Updated totalEpisodes to 72.")
    print("Response:", r.json())
else:
    print(f"FAILED: {r.status_code} - {r.text}")
