import requests
API_BASE = 'https://api.shortlovers.id'
DRAMA_ID = 'pjr00rw58d0y73bk7axn1buy'

r = requests.get(f"{API_BASE}/api/dramas/{DRAMA_ID}", timeout=10)
if r.ok:
    d = r.json()
    print("Drama Details:")
    print(f"  Title: {d.get('title')}")
    print(f"  Total Episodes in Metadata: {d.get('totalEpisodes')}")
    print(f"  Status: {d.get('status')}")
    print(f"  Is Active: {d.get('isActive')}")
else:
    print("Failed to fetch drama detail:", r.status_code)
