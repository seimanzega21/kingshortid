import requests
import urllib3
import json
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

VIDRAMA_API = 'https://vidrama.asia/api/netshortv2'
WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

target_keywords = ["Ikatan", "Cantik", "Kekuatan", "Abadi"]

found = []
# Search feed pages 1 to 50
for page in range(1, 51):
    print(f"Checking feed page {page}...")
    url = f"{VIDRAMA_API}/feed/{page}?lang=id_ID"
    try:
        r = requests.get(url, headers=WEB_HDRS, verify=False, timeout=10)
        data = r.json()
        items = data.get('data', [])
        if not items:
            print(f"Page {page} empty, stopping.")
            break
        for it in items:
            title = it.get('title', '')
            for kw in target_keywords:
                if kw.lower() in title.lower():
                    found.append(it)
                    print(f"MATCH: {title} (ID: {it.get('id')})")
                    break
    except Exception as e:
        print(f"Error on page {page}: {e}")
        break

print("\n--- SUMMARY ---")
if found:
    for f in found:
        print(f"Title: {f.get('title')}")
        print(f"ID: {f.get('id')}")
        print(f"Cover: {f.get('cover')}")
        print("-" * 20)
else:
    print("No matching drama found in feed.")
