# -*- coding: utf-8 -*-
import requests, urllib3, sys
urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

url = 'https://vidrama.asia/_next/static/chunks/123c8307fc6c5765.js'
r = requests.get(url, verify=False)
if r.ok:
    pos = 7018
    start = max(0, pos - 250)
    end = min(len(r.text), pos + 250)
    print("--- CONTEXT AROUND INDEX 7018 ---")
    print(r.text[start:end])
