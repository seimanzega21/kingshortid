import requests
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/'
}

r = requests.get('https://vidrama.asia/api/shortmax/detail/864494', headers=headers, verify=False)
data = r.json()
print(json.dumps(data, indent=2))
with open('shortmax_detail.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)
