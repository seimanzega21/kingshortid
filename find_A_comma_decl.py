# -*- coding: utf-8 -*-
import requests, re, urllib3, sys
urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

url = 'https://vidrama.asia/_next/static/chunks/123c8307fc6c5765.js'
r = requests.get(url, verify=False)
if r.ok:
    # Let's search for A followed by = and a single/double char function call
    # e.g., A = r(12345), A = a(12345), A = (0, r.A)(12345)
    for m in re.finditer(r'\bA\s*=\s*\w+\(\d+\)', r.text):
        print(f"Match: {m.group(0)} at {m.start()}")
    for m in re.finditer(r'\bA\s*=\s*\(\d+,\s*\w+\.\w+\)\(\d+\)', r.text):
        print(f"Match: {m.group(0)} at {m.start()}")
    for m in re.finditer(r'\bA\s*=\s*\w+\.\w+', r.text):
        print(f"Match: {m.group(0)} at {m.start()}")
