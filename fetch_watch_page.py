# -*- coding: utf-8 -*-
import requests
import urllib3
urllib3.disable_warnings()

WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

url = 'https://vidrama.asia/id/watch/reinkarnasi-pilot-ulung--7653295748544465973/1?provider=melolov3'
print("Fetching url:", url)
r = requests.get(url, headers=WEB_HDRS, timeout=15, verify=False)
print("Status:", r.status_code)
if r.ok:
    print("Content length:", len(r.text))
    # Save the html
    with open('watch_page_melolov3.html', 'w', encoding='utf-8') as f:
        f.write(r.text)
        
    # Scan for next-action in text
    print("\nScanning for Next.js actions:")
    import re
    # Find action names (hashes of length 40 in hex)
    actions = re.findall(r'[a-f0-9]{40}', r.text)
    print("Found potential action hashes (hex40):", set(actions))
    
    # Check if we can find any agilecdn or stream URLs
    urls = re.findall(r'https?://[^\s"\'>]+\.m3u8', r.text)
    print("\nFound m3u8 URLs:", urls[:5])
    
    # Check if there is a script tag with JSON
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', r.text, re.DOTALL)
    print(f"\nFound {len(scripts)} script tags.")
    for i, s in enumerate(scripts):
        if 'self.__next_f' in s:
            print(f"Script {i} contains __next_f! Length: {len(s)}")
else:
    print(r.text[:500])
