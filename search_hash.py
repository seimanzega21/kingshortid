# -*- coding: utf-8 -*-
import requests, urllib3, sys
urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

url = 'https://vidrama.asia/watch/satu-pedang-tebas-raja-neraka--19820/1?provider=stardusttv'
r = requests.get(url, headers=WEB_HDRS, timeout=15, verify=False)
if r.ok:
    print(f"HTML Length: {len(r.text)}")
    # Search for the hash
    hash_str = '59296e557a9949f4a8238ab67e431dad'
    if hash_str in r.text:
        print(f"FOUND HASH '{hash_str}' in HTML!")
    else:
        print(f"Hash '{hash_str}' NOT found in HTML.")
        
    # Search for parts of the URL
    for part in ['mmcdn', 'stardust-tv', 'DUB']:
        if part in r.text:
            print(f"FOUND PART '{part}' in HTML!")
        else:
            print(f"Part '{part}' NOT found in HTML.")
else:
    print(f"Error {r.status_code}")
