# -*- coding: utf-8 -*-
import requests, re, urllib3, sys
urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

url = 'https://vidrama.asia/_next/static/chunks/825014a8adcb9585.js'
r = requests.get(url, verify=False)
if r.ok:
    for num in ['7312634', '3927665']:
        matches = list(re.finditer(num + r'\s*:', r.text))
        print(f"Found {len(matches)} occurrences of '{num}:' in 825014a8adcb9585.js")
        for match in matches:
            start = match.start()
            end = min(len(r.text), match.end() + 2500)
            print(f"Module {num} definition:")
            print(r.text[start:end])
            print("="*60)
