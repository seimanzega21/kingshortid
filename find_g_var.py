# -*- coding: utf-8 -*-
import requests, re, urllib3, sys
urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

url = 'https://vidrama.asia/_next/static/chunks/123c8307fc6c5765.js'
r = requests.get(url, verify=False)
if r.ok:
    # Let's search for assignments of g
    # e.g., var g=e.i(...) or ,g=e.i(...)
    for m in re.finditer(r'\bg\s*=\s*e\.i\(\d+\)', r.text):
        print(f"Match: {m.group(0)} at {m.start()}")
    for m in re.finditer(r'\bg\s*=\s*\w+', r.text):
        if m.start() < 20000:
            print(f"Match2: {m.group(0)} at {m.start()}")
