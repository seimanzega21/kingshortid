import requests
import json
import urllib.parse
import re

API_BASE = 'https://api.shortlovers.id/api'

with open('netshortv2_feed.json', 'r', encoding='utf-8') as f:
    queue = json.load(f)

def clean_title(t):
    t = t.lower()
    t = re.sub(r'\[versi dub\]|\(sulih suara\)|\[dubbing\]|\[dijuluki\]', '', t)
    return re.sub(r'[^a-z0-9]', '', t)

dramas_found = []
for item in queue.get('data', []):
    title = item.get('title')
    if not title: continue
    words = title.replace('[Versi Dub]', '').replace('(Sulih Suara)', '').replace('[Dubbing]', '').replace('[Dijuluki]', '').split()
    if not words: continue
    q = ' '.join(words[:3])
    r = requests.get(f'{API_BASE}/dramas/search?q={urllib.parse.quote(q)}')
    if r.ok:
        dramas = r.json().get('dramas', [])
        my_clean = clean_title(title)
        matches = [d for d in dramas if clean_title(d['title']) == my_clean]
        if len(matches) > 1:
            print(f'DUPLICATES FOUND FOR: {title}')
            for m in matches:
                print(f"  - ID: {m['id']}, Title: {m['title']}, Cover: {m['cover']}, Active: {m['isActive']}")
