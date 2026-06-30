# -*- coding: utf-8 -*-
import requests, json, urllib3, sys
urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

r = requests.get('https://vidrama.asia/api/providers/settings', headers=WEB_HDRS, timeout=15, verify=False)
if r.ok:
    print(json.dumps(r.json(), indent=2))
else:
    print(f"Error {r.status_code}: {r.text}")
