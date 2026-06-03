import json

with open('all_dramas.json', 'r', encoding='utf-8') as f:
    dramas = json.load(f)

print(f"Total dramas in JSON: {len(dramas)}")
# Search for titles containing "Mendengar", "Hati", "Hearing", "Heart"
keywords = ["mendengar", "hati", "hearing", "heart"]
for kw in keywords:
    print(f"\nSearching for '{kw}':")
    matches = [d for d in dramas if kw in d.get('title', '').lower()]
    for m in matches:
        print(f"  - {m.get('title')} (ID: {m.get('id')})")
