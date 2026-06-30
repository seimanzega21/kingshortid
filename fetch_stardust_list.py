# -*- coding: utf-8 -*-
import requests, json, urllib3, sys
urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

url = 'https://vidrama.asia/api/stardusttv?action=combined&page=1&page_size=30&lang=id'
r = requests.get(url, headers=WEB_HDRS, timeout=10, verify=False)
if r.ok:
    data = r.json()
    items = data.get('data', [])
    print(f"Total stardusttv movies in ID: {len(items)}")
    
    # Save the full list
    with open('stardust_dramas_id.json', 'w', encoding='utf-8') as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
        
    for i, item in enumerate(items):
        print(f"\n{i+1}: ID={item.get('id')} | Title={item.get('title')} | Name={item.get('name')}")
        print(f"   Cover: {item.get('poster') or item.get('image')}")
        print(f"   Eps: {item.get('maxEps') or item.get('chapterCount') or item.get('loadedEpisodes')}")
else:
    print(f"Error: {r.status_code}")
