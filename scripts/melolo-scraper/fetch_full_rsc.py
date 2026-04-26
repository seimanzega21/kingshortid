import requests

url = 'https://vidrama.asia/movie/dubbingsopir-taksi-mantan-dewa-balap--846959?provider=shortmax&_rsc=1luph'
headers = {
    'rsc': '1',
    'sec-ch-ua-platform': '"Android"',
    'Referer': 'https://vidrama.asia/watch/dubbingsopir-taksi-mantan-dewa-balap--846959/1?provider=shortmax',
    'sec-ch-ua': '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
    'sec-ch-ua-mobile': '?1',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36'
}

r = requests.get(url, headers=headers)
print('Status:', r.status_code)
if r.status_code == 200:
    with open('d:/kingshortid/scripts/melolo-scraper/rsc_payload_full.txt', 'w', encoding='utf-8') as f:
        f.write(r.text)
    print('Payload length:', len(r.text))
else:
    print(r.text)
