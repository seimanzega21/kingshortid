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

video_id = "1ZkXla"

detail_url = f"https://vidrama.asia/api/proxy-cubetv/detail/{video_id}?lang=id"
episodes_url = f"https://vidrama.asia/api/proxy-cubetv/episodes/{video_id}?lang=id"

print("=== TESTING DETAIL ===")
r = requests.get(detail_url, headers=WEB_HDRS, verify=False, timeout=15)
print(f"Detail Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(json.dumps(data, indent=2))
else:
    print(r.text)

print("\n=== TESTING EPISODES ===")
r = requests.get(episodes_url, headers=WEB_HDRS, verify=False, timeout=15)
print(f"Episodes Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    eps = data if isinstance(data, list) else data.get('rows', data.get('data', []))
    print(f"Total episodes returned: {len(eps)}")
    if eps:
        print("First episode sample:")
        print(json.dumps(eps[0], indent=2))
        
        # Check if there is stream URL or watch details
        first_ep_id = eps[0].get('id')
        watch_url = f"https://vidrama.asia/api/proxy-cubetv/watch/{video_id}/{first_ep_id}?lang=id"
        print(f"\nProbing watch API for first ep id {first_ep_id}: {watch_url}")
        wr = requests.get(watch_url, headers=WEB_HDRS, verify=False, timeout=15)
        print(f"Watch Status: {wr.status_code}")
        if wr.status_code == 200:
            print(json.dumps(wr.json(), indent=2))
        else:
            print(wr.text)
else:
    print(r.text)
