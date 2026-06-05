import requests

API_BASE = 'https://api.shortlovers.id/api'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
headers = {'x-admin-key': ADMIN_KEY}

db_id = 'xmewhikaocggtjkchduc2qc0'

r = requests.get(f"{API_BASE}/dramas/{db_id}?includeInactive=true", headers=headers)
if r.ok:
    data = r.json()
    print("DRAMA INFO:")
    print("  Title:", data.get('title'))
    print("  Total Episodes in DB metadata:", data.get('totalEpisodes'))
    print("  Created At:", data.get('createdAt'))
    print("  Updated At:", data.get('updatedAt'))
    print("  Is Active:", data.get('isActive'))
else:
    print("Failed")
