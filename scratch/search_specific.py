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
if r.ok:
    data = r.json()
    items = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        d_val = data.get('data')
        if isinstance(d_val, list):
            items = d_val
        elif isinstance(d_val, dict):
            items = d_val.get('list', [])
        else:
            items = data.get('dramas', data.get('movies', []))
            
    print(f"Results: {len(items)}")
    for item in items:
        title = item.get('title') or item.get('videoName') or item.get('video_name')
        prov = item.get('_provider') or item.get('provider') or item.get('provider_id')
        vid = item.get('id') or item.get('videoid') or item.get('video_id')
        print(f"Title: {title} | Provider: {prov} | ID: {vid}")
else:
    print(r.status_code)
