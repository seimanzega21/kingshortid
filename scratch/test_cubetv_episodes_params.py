import requests
import json
import urllib3
import sys

urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

video_id = "QZpz60"

test_urls = [
    f"https://vidrama.asia/api/proxy-cubetv/episodes/{video_id}?lang=id",
    f"https://vidrama.asia/api/proxy-cubetv/episodes/{video_id}?lang=id&page=1&limit=100",
    f"https://vidrama.asia/api/proxy-cubetv/episodes/{video_id}?lang=id&pageNum=1&pageSize=100",
    f"https://vidrama.asia/api/proxy-cubetv/episodes/{video_id}?lang=id&page=1&size=100",
    f"https://vidrama.asia/api/proxy-cubetv/episodes/{video_id}?lang=id&limit=100",
    f"https://vidrama.asia/api/proxy-cubetv/episodes/{video_id}?lang=id&page=1"
]

for url in test_urls:
    print(f"\nTesting: {url}")
    r = requests.get(url, headers=headers, verify=False, timeout=15)
    print("Status:", r.status_code)
    if r.ok:
        data = r.json()
        print("Response Keys:", list(data.keys()))
        rows = data if isinstance(data, list) else data.get('rows', data.get('data', []))
        total = data.get('total') if isinstance(data, dict) else len(data)
        print(f"Total: {total}, Rows Count: {len(rows)}")
        if rows:
            print("First row sample:", json.dumps(rows[0])[:200])
    else:
        print(r.text)
