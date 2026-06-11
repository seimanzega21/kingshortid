import requests
import re
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/'
}

url = 'https://vidrama.asia/movie/sang-juara-menyamar-jadi-ob--7643677444247311367?provider=pine'
r = requests.get(url, headers=headers, verify=False, timeout=15)

# Search for the Next.js state data containing the cover
# Next.js App Router (Next 13/14+) push data looks like this: self.__next_f.push([1,"..."])
# Let's extract any URLs pointing to tiktokcdn from the response text
matches = re.findall(r'https://[^\s\"\'\>\\,]+tiktokcdn[^\s\"\'\>\\,]+', r.text)
print("--- Found TikTok CDN URLs in HTML ---")
for m in set(matches):
    print(m)
