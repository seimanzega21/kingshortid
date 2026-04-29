import requests, json, urllib3
urllib3.disable_warnings()

VIDRAMA_API = 'https://vidrama.asia/api/netshortv2'
WEB_HDRS = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://vidrama.asia/'}

dramas = [
    ('pemilik-kitab-pedang', '2036690458087784450'),
    ('jenderal-masakanku-siap', '2045396177699995650'),
    ('kode-cinta-robot', '2044326309693227010'),
    ('dia-kembali-dari-balik-legenda', '2011980833696841730'),
]

for slug, drama_id in dramas:
    r = requests.get(f'{VIDRAMA_API}/detail/{drama_id}?lang=id_ID', headers=WEB_HDRS, verify=False)
    detail = r.json().get('data', {})
    eps = detail.get('episodes', [])
    free = [e for e in eps if not e.get('isLocked')]
    locked = [e for e in eps if e.get('isLocked')]
    print(f"\n{detail.get('title')}")
    print(f"  Total: {len(eps)} | Free: {len(free)} | Locked (VIP): {len(locked)}")
    print(f"  Finished: {detail.get('isFinished')}")
