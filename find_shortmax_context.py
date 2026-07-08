# -*- coding: utf-8 -*-
import requests, urllib3, sys
urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

url = 'https://vidrama.asia/_next/static/chunks/123c8307fc6c5765.js'
r = requests.get(url, verify=False)
if r.ok:
    # Match 1 is at index 40920
    # Let's print 1500 characters before and 100 characters after index 40920
    pos = 40920
    start = max(0, pos - 2000)
    end = min(len(r.text), pos + 200)
    print("--- CONTEXT BEFORE MATCH 1 ---")
    print(r.text[start:end])
