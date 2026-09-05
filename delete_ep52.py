import requests

API_BASE  = 'http://141.11.160.187:3000'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}
DRAMA_ID_DB = 'kjhmxxf2mk12ulrr7eqcyl8m'

er = requests.get(f"{API_BASE}/api/dramas/{DRAMA_ID_DB}/episodes", timeout=15)
eps = sorted(er.json(), key=lambda x: int(x.get('episodeNumber', 0)))

ep52 = next((e for e in eps if int(e.get('episodeNumber', 0)) == 52), None)
ep51 = next((e for e in eps if int(e.get('episodeNumber', 0)) == 51), None)

if ep52:
    print(f"EP52 in DB: ID={ep52['id']}")
    print(f"  videoUrl: {ep52.get('videoUrl','')}")
    ep52_id = ep52['id']
    # Try delete
    for method_url in [
        f"{API_BASE}/api/admin/episodes/{ep52_id}",
        f"{API_BASE}/api/episodes/{ep52_id}",
        f"{API_BASE}/api/admin/dramas/{DRAMA_ID_DB}/episodes/{ep52_id}",
    ]:
        rd = requests.delete(method_url, headers=ADMIN_HDR, timeout=15)
        print(f"  DELETE {method_url.split('/')[-3:]}: {rd.status_code} {rd.text[:60]}")
        if rd.ok:
            print("  SUCCESS!")
            break

if ep51:
    print(f"\nEP51 in DB: ID={ep51['id']}")
    print(f"  videoUrl: {ep51.get('videoUrl','')}")
