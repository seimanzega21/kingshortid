# -*- coding: utf-8 -*-
import requests, re, urllib3, sys
urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

url = 'https://vidrama.asia/_next/static/chunks/123c8307fc6c5765.js'
r = requests.get(url, verify=False)
if r.ok:
    # Let's search for "shortmax" assignment or definition in the file
    # For example, let's find the places where shortmax is used to initialize an object.
    # In Next.js it might look like `shortmax: ...` or similar.
    # Let's find matches for "shortmax" and print the context.
    matches = list(re.finditer(r'shortmax', r.text))
    print(f"Found {len(matches)} occurrences of 'shortmax'")
    for match in matches:
        start = max(0, match.start() - 300)
        end = min(len(r.text), match.end() + 300)
        print(f"Match at {match.start()}:")
        print(r.text[start:end])
        print("="*60)
