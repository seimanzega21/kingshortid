# -*- coding: utf-8 -*-
import requests, re, urllib3, sys
urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

url = 'https://vidrama.asia/_next/static/chunks/123c8307fc6c5765.js'
r = requests.get(url, headers=WEB_HDRS, verify=False)
if r.ok:
    text = r.text
    print("Chunk length:", len(text))
    
    # Find all matches of 'melolov3' and print surrounding text
    for match in re.finditer(r'melolov3', text):
        start = max(0, match.start() - 200)
        end = min(len(text), match.end() + 200)
        print("--- MATCH AT INDEX", match.start(), "---")
        print(text[start:end])
        print("*" * 60)
else:
    print("Error:", r.status_code)
