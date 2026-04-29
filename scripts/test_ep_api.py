import requests, json
VIDRAMA_API = 'https://vidrama.asia/api/netshortv2'
WEB_HDRS = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://vidrama.asia/'}

for drama_id, label in [
    ('2036690458087784450', 'Pemilik Kitab Pedang'),
    ('2045396177699995650', 'Jenderal Masakanku Siap'),
]:
    r = requests.get(f'{VIDRAMA_API}/episode/{drama_id}/1?lang=id_ID', headers=WEB_HDRS, timeout=15)
    data = r.json()
    code = data.get('code')
    videos = data.get('data', {}).get('videos', [])
    print(f"\n{label} (code={code}, {len(videos)} qualities):")
    for v in videos:
        q = v.get('quality')
        u = v.get('url', '')[:80]
        print(f"  - {q}: {u}...")
