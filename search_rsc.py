# -*- coding: utf-8 -*-
import requests, urllib3, sys, re
urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
    'Accept': 'text/x-component',
    'Next-Router-State-Tree': '%5B%5B%22%22%2C%7B%22children%22%3A%5B%22watch%22%2C%7B%22children%22%3A%5B%22satu-pedang-tebas-raja-neraka--19820%22%2C%7B%22children%22%3A%5B%221%22%2C%7B%22children%22%3A%5B%22__PAGE__%22%2C%7B%7D%5D%7D%5D%7D%5D%7D%5D%7D%5D%7D%5D',
}

url = 'https://vidrama.asia/watch/satu-pedang-tebas-raja-neraka--19820/1?provider=stardusttv&_rsc=1ve02'
r = requests.get(url, headers=WEB_HDRS, timeout=15, verify=False)
if r.ok:
    print(f"RSC Length: {len(r.text)}")
    # Search for stardust or mmcdn or m3u8
    matches = re.findall(r'[^"\']*(?:stardust|mmcdn|m3u8)[^"\']*', r.text)
    print(f"Matches found ({len(matches)}):")
    for m in matches[:30]:
        print(f"  - {m[:120]}")
else:
    print(f"Error {r.status_code}")
