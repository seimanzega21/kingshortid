import requests

API_BASE = 'https://api.shortlovers.id'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

# Check if drama detail returns subtitles now
DRAMA_ID = 'qg3nrdawqa5ewa0vv1rysfoa'  # Sang Pewaris (should have subtitles)

r = requests.get(f"{API_BASE}/api/dramas/{DRAMA_ID}", headers=ADMIN_HDR, timeout=20)
if r.ok:
    eps = r.json().get('episodes', [])
    if eps:
        ep = eps[0]
        subs = ep.get('subtitles', [])
        print(f"Episode 1 subtitles: {len(subs)}")
        if subs:
            print(f"First sub: {subs[0].get('language')} - {subs[0].get('url', '')[:50]}...")
            print("API UPDATE SUCCESS - subtitles included!")
        else:
            print("Still NO subtitles - deploy may not be complete yet")
    else:
        print("No episodes")
else:
    print(f"Error: {r.status_code}")
