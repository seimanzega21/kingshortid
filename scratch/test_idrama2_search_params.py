import requests
import urllib3
import json

urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

params_list = [
    "q=Anak+Serigala",
    "query=Anak+Serigala",
    "search=Anak+Serigala",
    "keyword=Anak+Serigala&q=Anak+Serigala",
    "keyword=Anak+Serigala&query=Anak+Serigala",
]

for p in params_list:
    url = f"https://vidrama.asia/api/idrama2/search?{p}"
    print(f"\nTesting: {url}...")
    try:
        r = requests.get(url, headers=headers, verify=False, timeout=10)
        print(f"Status: {r.status_code}")
        if r.ok:
            try:
                data = r.json()
                print(json.dumps(data, indent=2))
            except:
                print("Text:", r.text[:150])
        else:
            print("Response:", r.text[:150])
    except Exception as e:
        print("Error:", e)
