import requests
import json
import re

url = 'https://vidrama.asia/provider/netshortv2'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

def main():
    print(f"Requesting: {url}")
    r = requests.get(url, headers=headers, timeout=20, verify=False)
    print(f"Status: {r.status_code}")
    if r.ok:
        m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', r.text)
        if m:
            data = json.loads(m.group(1))
            page_props = data.get('props', {}).get('pageProps', {})
            dramas = page_props.get('dramas', [])
            print(f"Total dramas found: {len(dramas)}")
            # Print title and id
            for d in dramas[:50]:
                print(f" - {d.get('title')} (ID: {d.get('id')})")
        else:
            print("__NEXT_DATA__ script not found in HTML")
    else:
        print("Failed to fetch HTML")

if __name__ == "__main__":
    main()
