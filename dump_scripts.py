# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
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
    soup = BeautifulSoup(r.text, 'html.parser')
    scripts = soup.find_all('script')
    print(f"Found {len(scripts)} script tags:")
    for i, s in enumerate(scripts):
        src = s.get('src')
        if src:
            print(f"  {i}: src={src}")
        else:
            text = s.string or s.text or ''
            print(f"  {i}: inline, len={len(text)}, content preview: {text[:200].strip()}")
else:
    print(f"Error {r.status_code}")
