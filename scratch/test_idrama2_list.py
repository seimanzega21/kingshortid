import requests
import urllib3
import json

urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

candidates = [
    "https://vidrama.asia/api/netshortv2/provider/idrama2?lang=id_ID",
    "https://vidrama.asia/api/netshortv2/provider?name=idrama2&lang=id_ID",
    "https://vidrama.asia/api/netshortv2/movies?provider=idrama2&lang=id_ID",
    "https://vidrama.asia/api/netshortv2/feed/1?provider=idrama2&lang=id_ID",
    "https://vidrama.asia/api/netshortv2/movie?provider=idrama2&lang=id_ID",
    "https://vidrama.asia/api/netshortv2/list?provider=idrama2&lang=id_ID",
    "https://vidrama.asia/api/netshortv2/search?provider=idrama2&lang=id_ID",
    "https://vidrama.asia/api/netshortv2/home?provider=idrama2&lang=id_ID",
    "https://vidrama.asia/api/netshortv2/provider/movies?name=idrama2&lang=id_ID",
    "https://vidrama.asia/api/netshortv2/provider/idrama2?page=1&size=20&lang=id_ID",
    "https://vidrama.asia/api/netshortv2/movie/provider/idrama2?lang=id_ID",
    "https://vidrama.asia/api/netshortv2/feed/1?lang=id_ID" # default feed
]

for url in candidates:
    print(f"\nProbing: {url}...")
    try:
        r = requests.get(url, headers=headers, verify=False, timeout=10)
        print(f"Status: {r.status_code}")
        if r.ok:
            data = r.json()
            code = data.get('code')
            print(f"Code: {code}, Message: {data.get('message') or data.get('msg')}")
            if code == 200 or 'data' in data:
                d = data.get('data')
                if isinstance(d, dict):
                    print(f"Keys: {list(d.keys())}")
                    for k in ['list', 'movies', 'items']:
                        if k in d:
                            print(f"  --> Found '{k}' of length {len(d[k])}")
                elif isinstance(d, list):
                    print(f"List length: {len(d)}")
                    if d:
                        print(f"  --> Sample: {str(d[0])[:150]}")
    except Exception as e:
        print("Error:", e)
