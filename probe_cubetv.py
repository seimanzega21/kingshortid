import requests
import json
import re

url = "https://vidrama.asia/movie/raja-jalan-raya--NZXDNZ?provider=cubetv&lang=id"
print(f"Fetching {url}")
hdrs = {"User-Agent": "Mozilla/5.0"}
r = requests.get(url, headers=hdrs)
print("Status:", r.status_code)

match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', r.text)
if match:
    data = json.loads(match.group(1))
    props = data.get("props", {}).get("pageProps", {})
    print("Found NEXT_DATA!")
    print(json.dumps(props, indent=2)[:2000])
else:
    print("No NEXT_DATA found.")
    
# Let's also check the actual watch page HTML
url_watch = "https://vidrama.asia/watch/raja-jalan-raya--NZXDNZ/1?provider=cubetv&lang=id"
print(f"\nFetching {url_watch}")
r_watch = requests.get(url_watch, headers=hdrs)
print("Status:", r_watch.status_code)

match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', r_watch.text)
if match:
    data = json.loads(match.group(1))
    props = data.get("props", {}).get("pageProps", {})
    print("Found NEXT_DATA in watch page!")
    # Just print the keys to avoid huge output
    print(list(props.keys()))
    if 'fallback' in props:
        for k in props['fallback']:
            print("Fallback key:", k)
            if 'watch' in k or 'stream' in k or 'episode' in k:
                print("Found stream data:", json.dumps(props['fallback'][k])[:500])
else:
    print("No NEXT_DATA found in watch page.")
