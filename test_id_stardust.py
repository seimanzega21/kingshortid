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

mid = '19163'
url = f'https://vidrama.asia/en/watch/some-slug--{mid}/1?provider=stardusttv'
hdrs = WEB_HDRS.copy()
hdrs['next-action'] = '60ea10e5421e7d8bbba1e0d453714768474e2a8880'

try:
    r = requests.post(url, headers=hdrs, data=json.dumps([mid, "id"]), timeout=15, verify=False)
    print(f"Status: {r.status_code}")
    if r.ok:
        for line in r.text.split('\n'):
            if '"title"' in line:
                content = line[line.find('{'):] if '{' in line else line
                data = json.loads(content)
                print(f"Title: {data.get('title')}")
                print(f"Episodes count: {len(data.get('episodes', []))}")
                # Check first episode stream url
                eps = data.get('episodes', [])
                if eps:
                    print(f"First episode video: {eps[0].get('_h264')}")
except Exception as e:
    print(f"Error: {e}")
