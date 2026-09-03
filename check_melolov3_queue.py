import requests
import json

API_BASE = 'http://141.11.160.187:3000'

# Load all 32 melolov3 dramas from queue
with open('new_melolov3_dramas.json', encoding='utf-8') as f:
    queue = json.load(f)

# Get existing DB titles
r = requests.get(f'{API_BASE}/api/dramas?limit=5000', timeout=60)
data = r.json()
dramas = data if isinstance(data, list) else data.get('dramas', [])
existing = {d.get('title','').lower().strip(): d for d in dramas}

print(f"Total dramas in DB: {len(dramas)}")
print(f"Total in melolov3 queue: {len(queue)}\n")

already_done = []
pending = []

for q in queue:
    slug = q['slug']
    # Try to match slug to title in DB
    slug_as_title = slug.replace('-', ' ')
    found = False
    for title_lower, d in existing.items():
        # Match if slug words appear in title or vice versa
        if slug_as_title in title_lower or all(word in title_lower for word in slug_as_title.split() if len(word) > 3):
            already_done.append({'slug': slug, 'db_title': d.get('title'), 'id': d.get('id'), 'eps': d.get('totalEpisodes')})
            found = True
            break
    if not found:
        pending.append(q)

print(f"=== ALREADY IN DB ({len(already_done)}) ===")
for d in already_done:
    print(f"  OK: {d['db_title']} ({d['eps']} eps)")

print(f"\n=== STILL PENDING ({len(pending)}) ===")
for i, p in enumerate(pending):
    print(f"  {i+1}. {p['slug']}")
