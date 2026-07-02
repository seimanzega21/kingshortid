import requests
import json
import urllib3
import sys

urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

keyword = "Bertani"
url = f"https://vidrama.asia/api/search/global?q={keyword}"

r = requests.get(url, headers=headers, verify=False, timeout=15)
print("Status:", r.status_code)
if r.ok:
    data = r.json()
    print("Raw Data:", json.dumps(data, indent=2))
else:
    print(r.text)
