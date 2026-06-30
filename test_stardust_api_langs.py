# -*- coding: utf-8 -*-
import requests, json, urllib3, sys
urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

# Test different lang codes
langs = ['id', 'id-ID', 'id_ID', 'in', 'en']

for lang in langs:
    url = f'https://vidrama.asia/api/stardusttv?action=combined&page=1&page_size=30&lang={lang}'
    print(f"\n--- TESTING LANG={lang} ---")
    try:
        r = requests.get(url, headers=WEB_HDRS, timeout=10, verify=False)
        print(f"Status: {r.status_code}")
        if r.ok:
            data = r.json()
            items = data.get('data', [])
            print(f"Items count: {len(items)}")
            for item in items[:5]:
                print(f"  ID: {item.get('id')} | Title: {item.get('title')} | Name: {item.get('name')}")
    except Exception as e:
        print(f"Error: {e}")
