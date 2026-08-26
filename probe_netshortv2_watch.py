import requests
import re
import urllib3
urllib3.disable_warnings()

url = "https://vidrama.asia/watch/dewa-petir-sss-tersembunyi--2089169768653586433/1?provider=netshortv2&lang=id_ID"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

r = requests.get(url, headers=headers, timeout=15, verify=False)
html = r.text

print(f"Watch page Status: {r.status_code}")
print("Let's look for video or API endpoints in the watch page:")

# Find m3u8 or mp4
m3u8s = re.findall(r'https?://[^\s\"\'\\]+\.m3u8[^\s\"\'\\]*', html)
if m3u8s:
    print("Found m3u8:")
    for m in set(m3u8s):
        print(m)

# Find .vtt
vtts = re.findall(r'https?://[^\s\"\'\\]+\.vtt[^\s\"\'\\]*', html)
if vtts:
    print("Found vtt:")
    for m in set(vtts):
        print(m)

# Find any API endpoints
apis = re.findall(r'https?://[^\s\"\'\\]*api[^\s\"\'\\]*', html)
if apis:
    print("Found APIs:")
    for m in set(apis):
        print(m)

print("Look for netshortv2 specific:")
matches = re.findall(r'.{0,50}netshortv2.{0,50}', html)
for m in set(list(matches)[:5]):
    print(m.strip())
    
