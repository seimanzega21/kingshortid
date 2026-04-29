import requests, urllib3, json
urllib3.disable_warnings()

WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://vidrama.asia/',
}

url = "https://vidrama.asia/api/netshortv2/feed/1?lang=id_ID"
r = requests.get(url, headers=WEB_HDRS, verify=False)
if r.ok:
    data = r.json().get('data', [])
    if data:
        print(json.dumps(data[0], indent=2))
