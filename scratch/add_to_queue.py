import json
from pathlib import Path

QUEUE_PATH = Path(r'd:\kingshortid\scripts\reelshort_queue.json')
with open(QUEUE_PATH, 'r', encoding='utf-8') as f:
    queue = json.load(f)

TARGET_ID = '6a0572b216e8f854a6012561'
found = False
for item in queue:
    if item['id'] == TARGET_ID:
        item['status'] = 'pending'
        item['processedAt'] = None
        found = True
        print('Reset ke pending:', item['title'])
        break

if not found:
    queue.append({
        'id': TARGET_ID,
        'title': '[Versi Dub] Ratu Kuliner: Resep Balas Dendam',
        'status': 'pending',
        'addedAt': '2026-06-09T07:11:00Z',
        'processedAt': None
    })
    print('Ditambahkan ulang: [Versi Dub] Ratu Kuliner: Resep Balas Dendam')

with open(QUEUE_PATH, 'w', encoding='utf-8') as f:
    json.dump(queue, f, indent=2, ensure_ascii=False)

pending = [i for i in queue if i['status'] == 'pending']
print(f'Total pending: {len(pending)}')
for p in pending:
    t = p['title']
    print(f'  -> {t}')
