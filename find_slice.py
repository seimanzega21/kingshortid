# -*- coding: utf-8 -*-
import requests, urllib3, sys
urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

url = 'https://vidrama.asia/_next/static/chunks/123c8307fc6c5765.js'
r = requests.get(url, verify=False)
if r.ok:
    pos = 40920
    start = max(0, pos - 5000)
    end = min(len(r.text), pos + 1000)
    with open('chunk_slice.js', 'w', encoding='utf-8') as f:
        f.write(r.text[start:end])
    print("Slice saved to chunk_slice.js. Length:", end - start)
