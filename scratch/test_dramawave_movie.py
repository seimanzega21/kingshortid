# -*- coding: utf-8 -*-
import requests
import urllib3
import sys

urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

movie_id = 'ahTFgKtAU6'

for p in ['dramawave', 'dramawavev2', 'netshort', 'netshortv2']:
    url = f"https://vidrama.asia/api/netshortv2/movie/{movie_id}?provider={p}&lang=id_ID"
    try:
        r = requests.get(url, headers=headers, timeout=15, verify=False)
        print(f"Provider: {p} -> Status: {r.status_code}")
        if r.ok:
            data = r.json()
            print(f"  Code: {data.get('code')}, Message: {data.get('message') or data.get('msg')}")
            if data.get('code') == 200:
                print("  Success! Data keys:", data.get('data', {}).keys())
                print("  Title:", data.get('data', {}).get('title'))
                print("  Episodes count:", len(data.get('data', {}).get('episodes', [])))
        else:
            print("  Text response:", r.text[:100])
    except Exception as e:
        print(f"  Exception: {e}")
