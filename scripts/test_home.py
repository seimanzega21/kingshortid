import requests
WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
    'Referer': 'https://vidrama.asia/',
}
r = requests.get('https://vidrama.asia/api/netshortv2/home?lang=id_ID', headers=WEB_HDRS, verify=False)
try:
    data = r.json()
    print("KEYS in data:", data.keys())
    if 'data' in data:
        print("KEYS in data['data']:", data['data'].keys())
        if 'modules' in data['data']:
            print("First module keys:", data['data']['modules'][0].keys())
        if 'list' in data['data']:
            print("list keys:", len(data['data']['list']))
except Exception as e:
    print("Error:", e, r.text)
