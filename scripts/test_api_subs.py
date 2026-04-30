import requests
import json

VIDRAMA_API = 'https://vidrama.asia/api/netshortv2'
drama_id = '2045396177699995650'
ep_no = 1

url = f"{VIDRAMA_API}/episode/{drama_id}/{ep_no}?lang=id_ID"
WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

r = requests.get(url, headers=WEB_HDRS, verify=False)
try:
    data = r.json()
    print(json.dumps(data, indent=2))
except:
    print(r.text)
