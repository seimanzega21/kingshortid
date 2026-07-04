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
    
    # We want to find getSeriesDetail as a property definition, e.g. "getSeriesDetail:" or "getSeriesDetail ="
    # Let's search for matches in the whole chunk
    for pattern in [r'getSeriesDetail\s*[:=]', r'getMultiVideo\s*[:=]']:
        print(f"--- Searching for pattern: {pattern} ---")
        for match in re.finditer(pattern, text):
            start = max(0, match.start() - 150)
            end = min(len(text), match.end() + 250)
            print(f"Match at {match.start()}:")
            print(text[start:end])
            print("*" * 60)
else:
    print("Error:", r.status_code)
