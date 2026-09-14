#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fetch Drama Details
"""
import requests, json, urllib3
urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/'
}

url = 'https://vidrama.asia/api/netshortv2/detail/2096782583337111554?lang=id_ID'
r = requests.get(url, headers=headers, verify=False, timeout=15)
print('STATUS:', r.status_code)
try:
    data = r.json()
    print('CODE:', data.get('code'))
    drama_data = data.get('data')
    if drama_data:
        print('TITLE:', drama_data.get('title'))
        print('TOTAL_EPS:', drama_data.get('totalEpisodes'))
        print('COVER:', drama_data.get('cover'))
        print('LABELS:', drama_data.get('labels'))
        print('FINISHED:', drama_data.get('isFinished'))
        with open('scripts/desainer_top_detail.json', 'w', encoding='utf-8') as f:
            json.dump(drama_data, f, indent=2, ensure_ascii=False)
        print('Detail saved to scripts/desainer_top_detail.json')
    else:
        print('RAW DATA:', data)
except Exception as e:
    print('ERROR:', e)
    print('TEXT PREVIEW:', r.text[:300])
