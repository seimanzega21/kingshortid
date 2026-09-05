import requests
hdrs = {'User-Agent': 'Mozilla/5.0'}
mid = '42000025364'

for ep in [0, 1, 2, 51, 52]:
    r = requests.get(f'https://vidrama.asia/api/dramabox?action=stream&id={mid}&episode={ep}&lang=in', headers=hdrs, timeout=15)
    print(f"episode={ep}: HTTP {r.status_code}", end="")
    if r.ok:
        d = r.json().get('data', {})
        vurl = d.get('videoUrl', '')
        # Get just the episode param from URL
        import urllib.parse
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(vurl).query)
        backend_ep = qs.get('episode', ['?'])[0]
        print(f" | backend episode={backend_ep}", end="")
        if vurl:
            rt = requests.head(vurl, headers=hdrs, timeout=8)
            print(f" | backend HTTP {rt.status_code}", end="")
    else:
        err = r.json().get('error', r.text[:60])
        print(f" | ERROR: {err}", end="")
    print()
