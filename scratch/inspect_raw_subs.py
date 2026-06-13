# -*- coding: utf-8 -*-
import requests, json

UPSTREAM_ID = '160000641572'
ep_no = 1
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://vidrama.asia/',
}
url = f"https://vidrama.asia/api/idrama2/unlock/{UPSTREAM_ID}/{ep_no}?lang=id"
resp = requests.get(url, headers=HEADERS, verify=False, timeout=20)
if resp.ok:
    data = resp.json().get('target_ep_info', {})
    print("screentext_list:")
    print(json.dumps(data.get('screentext_list'), indent=2))
    print("\nsubtitle_list:")
    print(json.dumps(data.get('subtitle_list'), indent=2))
