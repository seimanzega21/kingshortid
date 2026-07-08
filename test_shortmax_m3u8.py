# -*- coding: utf-8 -*-
import requests
import urllib3
urllib3.disable_warnings()

url = "https://volcengine-forward.shorttv.live/hls/394d8155-5433-4126-8f4d-a2541c11b1b8_720/main.m3u8?auth_key=1783480858-0-0-43dbbf46140234836a20e204395e60b6"
print("Fetching playlist from:", url)
try:
    r = requests.get(url, timeout=15, verify=False)
    print("Status:", r.status_code)
    print("Content-Type:", r.headers.get('Content-Type'))
    print("Content:")
    print(r.text[:500])
except Exception as e:
    print("Error:", e)
