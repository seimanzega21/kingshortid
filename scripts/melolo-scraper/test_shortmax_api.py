import requests

headers = {
    'accept': 'application/json, text/plain, */*',
    'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36',
    'origin': 'https://vidrama.asia',
    'referer': 'https://vidrama.asia/'
}

urls = [
    'https://vidrama.asia/api/shortmax?action=list&lang=id',
    'https://vidrama.asia/api/shortmax?action=detail&id=dubbingsopir-taksi-mantan-dewa-balap--846959',
    'https://vidrama.asia/api/shortmax?action=detail&id=846959'
]

for url in urls:
    print(f"\nTesting {url}")
    try:
        r = requests.get(url, headers=headers, timeout=5)
        print(f"Status: {r.status_code}")
        print(r.text[:200])
    except Exception as e:
        print(f"Error: {e}")
