# -*- coding: utf-8 -*-
import json, sys

sys.stdout.reconfigure(encoding='utf-8')

with open('stardust_dramas_id.json', 'r', encoding='utf-8') as f:
    dramas = json.load(f)

print(f"Total dramas in JSON: {len(dramas)}")

# Group by title to see duplicates
by_title = {}
for d in dramas:
    title = d.get('title')
    if title not in by_title:
        by_title[title] = []
    by_title[title].append(d)

print("\nDramas by title:")
for title, items in by_title.items():
    print(f"'{title}': {len(items)} version(s)")
    for i, item in enumerate(items):
        print(f"  Version {i+1}: ID={item.get('id')} | Name={item.get('name')} | Poster={item.get('poster') or item.get('image')}")
