import requests
import json
import urllib3
import sys

urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

# Test 1: slug in movie endpoint
slugs = ["gila-untuk-mencintai--1ZkXla", "1ZkXla"]
for s in slugs:
    url = f"https://vidrama.asia/api/netshortv2/movie/{s}?provider=cubetv&lang=id"
    print(f"\n--- Testing URL: {url} ---")
    try:
        r = requests.get(url, headers=WEB_HDRS, verify=False, timeout=10)
        print("Status Code:", r.status_code)
        if r.ok:
            data = r.json()
            print("Response Keys:", list(data.keys()))
            if 'data' in data:
                mdata = data['data']
                print("Title:", mdata.get('title'))
                print("Intro:", mdata.get('introduction'))
                print("Cover:", mdata.get('cover'))
                print("Genres:", mdata.get('genres'))
                eps = mdata.get('episodes', [])
                print(f"Total Episodes: {len(eps)}")
                if eps:
                    print("Sample Episode 1:", eps[0])
            else:
                print("Response Snippet:", json.dumps(data)[:300])
        else:
            print("Error:", r.text[:300])
    except Exception as e:
        print("Exception:", e)
