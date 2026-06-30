# -*- coding: utf-8 -*-
import requests, json, urllib3, sys
urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
    'Accept': 'text/x-component',
    'Content-Type': 'text/plain;charset=UTF-8',
}

mid = '19613'
url = f'https://vidrama.asia/en/watch/slug--{mid}/1?provider=stardusttv'
hdrs = WEB_HDRS.copy()
hdrs['next-action'] = '60ea10e5421e7d8bbba1e0d453714768474e2a8880'

r = requests.post(url, headers=hdrs, data=json.dumps([mid, "id"]), timeout=15, verify=False)
for line in r.text.splitlines():
    line = line.strip()
    if line.startswith('1:'):
        obj = json.loads(line[2:])
        list_val = obj.get('list')
        print(f"Type of 'list': {type(list_val).__name__}")
        if isinstance(list_val, list):
            print(f"List length: {len(list_val)}")
            print(f"First item: {json.dumps(list_val[0], indent=2)}")
