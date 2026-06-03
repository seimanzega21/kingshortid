import requests

API_BASE = 'https://api.shortlovers.id'
DRAMA_ID = 'pjr00rw58d0y73bk7axn1buy'

url = f"{API_BASE}/api/dramas/{DRAMA_ID}/episodes?includeInactive=true"
r = requests.get(url, timeout=10)
if r.ok:
    eps = r.json()
    ep_list = eps if isinstance(eps, list) else eps.get('episodes', eps.get('data', []))
    ep1 = next((e for e in ep_list if e.get('episodeNumber') == 1), None)
    if ep1:
        print("EP 1 detail:")
        print(f"  ID: {ep1.get('id')}")
        print(f"  Title: {ep1.get('title')}")
        print(f"  Video URL: {ep1.get('videoUrl')}")
        print(f"  Video 540p URL: {ep1.get('videoUrl540p')}")
    else:
        print("EP 1 not found in local db")
else:
    print("Failed to fetch:", r.status_code)
