import json

with open('scripts/melolov3_queue.json', 'r', encoding='utf-8') as f:
    q = json.load(f)

for i, x in enumerate(q[43:], 1):
    print(f"{i}. {x['title']} ({x['totalEpisodes']} eps) -> {x['status']}")
