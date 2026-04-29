"""
Fetch /watch page RSC data with the _rsc header and parse it for video URLs.
"""
import requests
import re
import json

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/x-component,application/json',
    'RSC': '1',
    'Next-Router-State-Tree': '%5B%22%22%2C%7B%22children%22%3A%5B%22__PAGE__%22%2C%7B%7D%5D%7D%2Cnull%2Cnull%2Ctrue%5D',
    'Next-Url': '/watch/pemilik-kitab-pedang--2036690458087784450/1',
    'Referer': 'https://vidrama.asia/movie/pemilik-kitab-pedang--2036690458087784450?provider=netshortv2&lang=id_ID',
}

URL = "https://vidrama.asia/watch/pemilik-kitab-pedang--2036690458087784450/1?provider=netshortv2&_rsc=1"
r = requests.get(URL, headers=HEADERS)
text = r.text
print(f"Status: {r.status_code}")
print(f"Response len: {len(text)}")

# Find all URLs in the response
mp4 = re.findall(r'https?://[^\s"\'\\]+\.mp4[^\s"\'\\]*', text)
m3u8 = re.findall(r'https?://[^\s"\'\\]+\.m3u8[^\s"\'\\]*', text)
netshort = re.findall(r'https?://[^\s"\'\\]*netshort\.com[^\s"\'\\]*', text)

print(f"\nMP4 URLs ({len(mp4)}):")
for u in mp4[:5]: print(f"  {u}")
print(f"\nM3U8 URLs ({len(m3u8)}):")
for u in m3u8[:5]: print(f"  {u}")
netshort_unique = list(set(netshort))
print(f"\nNetshort URLs ({len(netshort_unique)}):")
for u in netshort_unique[:10]: print(f"  {u}")

# Look for videoUrl field
for field in ['videoUrl', 'playUrl', 'streamUrl', 'hlsUrl', 'mp4Url']:
    idx = text.find(field)
    if idx >= 0:
        print(f"\nField '{field}' found at idx {idx}:")
        print(f"  {text[idx:idx+300]}")

# Print first 2000 chars of response
print(f"\n--- Response snippet ---")
print(text[:2000])
