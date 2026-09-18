import json
from pathlib import Path

p_queue = Path('scripts/melolov3_queue.json')
with open(p_queue, 'r', encoding='utf-8') as f:
    queue = json.load(f)

with open('top_10_additional_melolov3.json', 'r', encoding='utf-8') as f:
    additional_10 = json.load(f)

existing_ids = {item['id'] for item in queue}
added = 0
for d in additional_10:
    if d['id'] not in existing_ids:
        queue.append(d)
        added += 1
    else:
        for item in queue:
            if item['id'] == d['id']:
                item['status'] = 'pending'

with open(p_queue, 'w', encoding='utf-8') as f:
    json.dump(queue, f, indent=2, ensure_ascii=False)

print(f"Appended! Total queue: {len(queue)}, newly added: {added}")
