import json
from pathlib import Path

with open('scripts/melolov3_queue.json', 'r', encoding='utf-8') as f:
    q = json.load(f)

for i, x in enumerate(q[43:], 1):
    title = x['title']
    exp = x['totalEpisodes']
    p = Path(f"D:/Video Drama/Facebook/{title}")
    count = len(list(p.glob("*.mp4"))) if p.exists() else 0
    print(f"{i}. {title} | {count}/{exp} eps | status: {x['status']}")
