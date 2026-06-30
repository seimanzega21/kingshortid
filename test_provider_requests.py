# -*- coding: utf-8 -*-
import requests, urllib3, sys, re
urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
    'Cookie': 'global_ui_lang=id; next-locale=id; NEXT_LOCALE=id; lang=id',
}

url = 'https://vidrama.asia/provider/stardusttv?lang=id'
r = requests.get(url, headers=WEB_HDRS, timeout=15, verify=False)
if r.ok:
    print(f"Content Length: {len(r.text)}")
    # Find all movie matches
    matches = re.findall(r'/movie/[a-zA-Z0-9%\-]+--\d+', r.text)
    print(f"Found {len(matches)} movie matches in raw HTML:")
    for m in set(matches):
        print(f"  - {m}")
else:
    print(f"Error {r.status_code}")
