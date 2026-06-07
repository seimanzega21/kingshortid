# -*- coding: utf-8 -*-
import requests
import urllib3
import sys
import json

urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

found = False
for page in range(1, 20):
    url = f"https://vidrama.asia/api/netshortv2/feed/{page}?provider=dramawave&lang=id_ID"
    try:
        r = requests.get(url, headers=headers, verify=False, timeout=15)
        if r.ok:
            items = r.json().get('data', [])
            if not items:
                print(f"Page {page} is empty. Stopping.")
                break
            print(f"Page {page}: Loaded {len(items)} items")
            for item in items:
                title = item.get('title', '')
                item_id = item.get('id', '')
                if 'Penyembuh' in title or 'istri' in title.lower() or 'ahTFgKtAU6' in item_id:
                    print(f"  [+] FOUND: {title} | ID: {item_id} | Episodes: {item.get('totalEpisodes')}")
                    found = True
        else:
            print(f"Page {page} error: {r.status_code}")
    except Exception as e:
        print(f"Page {page} exception: {e}")

if not found:
    print("Drama 'Penyembuh Istrinya' not found in any feed page.")
