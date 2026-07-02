import requests
import json
import urllib3
import sys

urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

url = "https://vidrama.asia/api/proxy-cubetv/episodes/QZpz60?lang=id"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

r = requests.get(url, headers=headers, verify=False, timeout=15)
print("Status:", r.status_code)
if r.ok:
    print("Content (first 1000 chars):")
    print(r.text[:1000])
else:
    print(r.text)
