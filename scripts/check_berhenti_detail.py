import requests

API_BASE = 'https://api.shortlovers.id'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

DRAMA_ID = 'r22zs10yvkmoq0vqn5sxofqz'

r = requests.get(f"{API_BASE}/api/dramas/{DRAMA_ID}", headers=ADMIN_HDR, timeout=20)
if r.ok:
    d = r.json()
    print(f"Judul: {d.get('title')}")
    print(f"totalEpisodes: {d.get('totalEpisodes')}")
    print(f"isActive: {d.get('isActive')}")
    eps = d.get('episodes', [])
    print(f"Episodes with data: {len(eps)}")
    with_sub = sum(1 for ep in eps if ep.get('subtitles') and len(ep.get('subtitles',[]))>0)
    print(f"With subtitle: {with_sub}")
    with_video = sum(1 for ep in eps if ep.get('videoUrl'))
    print(f"With video: {with_video}")
else:
    print(f'Gagal: {r.status_code}')
