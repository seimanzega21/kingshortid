# -*- coding: utf-8 -*-
import requests, re, urllib3, sys
urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

url = 'https://vidrama.asia/_next/static/chunks/123c8307fc6c5765.js'
r = requests.get(url, verify=False)
if r.ok:
    # Find all occurrences of getDramaDetail in the chunk
    matches = list(re.finditer(r'getDramaDetail', r.text))
    print(f"Found {len(matches)} occurrences of 'getDramaDetail'")
    for match in matches:
        start = max(0, match.start() - 150)
        end = min(len(r.text), match.end() + 200)
        print(f"Match at {match.start()}:")
        print(r.text[start:end])
        print("="*60)
