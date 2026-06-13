import requests
import urllib3
import json

urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

urls = [
    "https://vidrama.asia/api/providers/settings",
    "https://vidrama.asia/api/server2/status"
]

for url in urls:
    print(f"\nFetching: {url}...")
    try:
        r = requests.get(url, headers=headers, verify=False, timeout=10)
        print(f"Status: {r.status_code}")
        if r.ok:
            try:
                data = r.json()
                print(json.dumps(data, indent=2))
            except Exception as e:
                print("Error decoding JSON:", e)
                print("Text response (first 200):", r.text[:200])
        else:
            print("Text response (first 200):", r.text[:200])
    except Exception as e:
        print("Error fetching:", e)
