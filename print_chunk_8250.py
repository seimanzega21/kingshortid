# -*- coding: utf-8 -*-
import requests, urllib3, sys
urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

url = 'https://vidrama.asia/_next/static/chunks/825014a8adcb9585.js'
r = requests.get(url, headers=WEB_HDRS, verify=False)
if r.ok:
    text = r.text
    idx = 40320
    start = max(0, idx - 3000)
    end = min(len(text), idx - 1800)
    print(text[start:end])
else:
    print("Error:", r.status_code)
