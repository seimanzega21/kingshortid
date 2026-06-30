# -*- coding: utf-8 -*-
import requests, json, urllib3, sys
urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

ID = '19820'
PROVIDER = 'stardusttv'

urls = [
    f"https://vidrama.asia/api/netshortv2/movie/{ID}?provider={PROVIDER}&lang=id_ID",
    f"https://vidrama.asia/api/netshortv2/movie/{ID}?provider={PROVIDER}&lang=in",
    f"https://vidrama.asia/api/netshortv2/detail/{ID}?provider={PROVIDER}&lang=id_ID",
    f"https://vidrama.asia/api/netshortv2/episode/{ID}/1?provider={PROVIDER}&lang=id_ID",
]

for url in urls:
    print(f"\nTesting: {url}")
    try:
        r = requests.get(url, headers=WEB_HDRS, timeout=10, verify=False)
        print(f"  Status: {r.status_code}")
        if r.ok:
            try:
                data = r.json()
                print(f"  Response (first 300 chars): {json.dumps(data, ensure_ascii=False)[:300]}")
            except:
                print(f"  Text (first 300 chars): {r.text[:300]}")
    except Exception as e:
        print(f"  Error: {e}")
