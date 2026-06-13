import requests
import urllib3
import json

urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

keywords = [
    "Anak Serigala",
    "Serigala Presiden",
    "Aku Lahirkan",
    "Lahirkan Anak",
    "Aku Lahirkan Anak Serigala"
]

for kw in keywords:
    url = f"https://vidrama.asia/api/idrama2/search?keyword={requests.utils.quote(kw)}"
    print(f"\nSearching for '{kw}': {url}...")
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
