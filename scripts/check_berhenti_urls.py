import requests

API_BASE = 'https://api.shortlovers.id'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

DRAMA_ID = 'r22zs10yvkmoq0vqn5sxofqz'

print('=== CEK URL VIDEO EPISODE BERHENTI BERJUDI ===')
r = requests.get(f"{API_BASE}/api/dramas/{DRAMA_ID}/episodes", headers=ADMIN_HDR, timeout=20)
if r.ok:
    data = r.json()
    eps = data if isinstance(data, list) else data.get('episodes', [])
    for ep in eps[:5]:
        url = ep.get('videoUrl', '')
        host = url.split('/')[2] if url else 'none'
        ep_no = ep.get('episodeNumber')
        print(f"ep{ep_no:02d}: host={host}, url={url[:60]}...")
        
        # Test accessibility
        try:
            head = requests.head(url, timeout=10, verify=False, allow_redirects=True)
            print(f"       status={head.status_code}, accessible={'yes' if head.status_code < 400 else 'NO'}")
        except Exception as e:
            print(f"       ERROR: {e}")
else:
    print(f'Gagal: {r.status_code}')
