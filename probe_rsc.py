import requests
import json
import urllib3
urllib3.disable_warnings()

url = "https://vidrama.asia/watch/dewa-petir-sss-tersembunyi--2089169768653586433/1?provider=netshortv2&lang=id_ID&_rsc=123"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Rsc': '1',
    'Next-Router-State-Tree': '%5B%22%22%2C%7B%22children%22%3A%5B%22watch%22%2C%7B%22children%22%3A%5B%5B%22slug%22%2C%22dewa-petir-sss-tersembunyi--2089169768653586433%22%2C%22d%22%5D%2C%7B%22children%22%3A%5B%5B%22episode%22%2C%221%22%2C%22d%22%5D%2C%7B%22children%22%3A%5B%22__PAGE__%22%2C%7B%7D%2Cnull%2Cnull%2Cfalse%5D%7D%2Cnull%2Cnull%2Cfalse%5D%7D%2Cnull%2Cnull%2Cfalse%5D%7D%2Cnull%2C%22refetch%22%2Cfalse%5D%7D%2Cnull%2Cnull%2Ctrue%5D'
}

r = requests.get(url, headers=headers, timeout=10, verify=False)
print(f"RSC Status: {r.status_code}")
print(f"Content-Type: {r.headers.get('Content-Type')}")

text = r.text
print(f"Length: {len(text)}")
import re

m3u8s = re.findall(r'https?://[^\s\"\'\\]+\.m3u8[^\s\"\'\\]*', text)
if m3u8s:
    print("Found m3u8:")
    for m in set(m3u8s):
        print(m)
else:
    print("No m3u8 found.")

vtts = re.findall(r'https?://[^\s\"\'\\]+\.vtt[^\s\"\'\\]*', text)
if vtts:
    print("Found vtt:")
    for m in set(vtts):
        print(m)
        
with open('rsc.txt', 'w', encoding='utf-8') as f:
    f.write(text)
