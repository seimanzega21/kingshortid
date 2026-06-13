import requests
import urllib3
import json

urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

# Correct upstream ID found in search results
correct_id = '160001641891'

endpoints = [
    f"https://vidrama.asia/api/idrama2/drama/{correct_id}?lang=id",
    f"https://vidrama.asia/api/idrama2/unlock/{correct_id}/1?lang=id",
]

for url in endpoints:
    print(f"\nProbing: {url}...")
    try:
        r = requests.get(url, headers=headers, verify=False, timeout=10)
        print(f"Status: {r.status_code}")
        if r.ok:
            data = r.json()
            print(json.dumps(data, indent=2))
        else:
            print("Response:", r.text[:200])
    except Exception as e:
        print("Error:", e)
