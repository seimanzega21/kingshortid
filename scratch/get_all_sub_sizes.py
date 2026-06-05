import requests
import sys

sys.stdout.reconfigure(encoding='utf-8')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/'
}
url = 'https://vidrama.asia/api/proxy-cubetv/episodes/20QkmZ?lang=id'

try:
    r = requests.get(url, headers=headers, verify=False, timeout=15)
    if r.status_code == 200:
        data = r.json()
        eps = data if isinstance(data, list) else data.get('rows', data.get('data', []))
        print("=== INDONESIAN SUBTITLE SIZES AT SOURCE ===")
        for ep in eps:
            ep_no = ep.get('episodeNumber')
            subs = ep.get('subtitles', [])
            id_sub = next((s for s in subs if s.get('lang') == 'id'), None)
            if id_sub:
                url_src = id_sub.get('url')
                r_sub = requests.head(url_src, timeout=10)
                size = r_sub.headers.get('Content-Length', '0')
                print(f"  - Episode {ep_no:02d}: size = {size} bytes")
            else:
                print(f"  - Episode {ep_no:02d}: NO INDONESIAN SUBTITLE URL")
except Exception as e:
    print("Error:", e)
