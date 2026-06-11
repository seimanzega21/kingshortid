import requests
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/'
}

# Search for OB
r = requests.get('https://vidrama.asia/api/search/global?q=OB', headers=headers, verify=False, timeout=15)
data = r.json()
print("--- Search Result for OB ---")
print(json.dumps(data, indent=2))
