# -*- coding: utf-8 -*-
import requests, urllib3, sys
urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

url = "https://tobrutmelolo.inicdn.net/api/v1/video/stream?id=7653370177773390853&auth_key=1783555200-0-0-d84006863b14e3154b2d7745d3a566eb"
WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

print("Checking URL headers...")
try:
    # Allow redirects, but we can print the history
    r = requests.get(url, headers=WEB_HDRS, stream=True, verify=False, timeout=15)
    print("Final Status:", r.status_code)
    print("Redirect history:")
    for h in r.history:
        print(f"  {h.status_code} -> {h.headers.get('Location')}")
    print("Final Headers:")
    for k, v in r.headers.items():
        print(f"  {k}: {v}")
    
    # Read first 100 bytes to see file type
    chunk = next(r.iter_content(100))
    print(f"First 100 bytes: {chunk[:100]}")
except Exception as e:
    print("Error:", e)
