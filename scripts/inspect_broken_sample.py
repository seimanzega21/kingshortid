import json, requests

with open('broken_covers.json', 'r', encoding='utf-8') as f:
    broken = json.load(f)

print(f"Total broken: {len(broken)}")
# Sample 15 titles
for i, b in enumerate(broken[:15], 1):
    print(f"{i}. {b['title']} -> {b['cover']}")
