import json
from pathlib import Path

QUEUE_PATH = Path(r'd:\kingshortid\scripts\reelshort_queue.json')

with open(QUEUE_PATH, 'r', encoding='utf-8') as f:
    queue = json.load(f)

new_drama = {
    'id': '69fab9d7b5b22259190f00f8',
    'title': '[Versi Dub] Di Dunia Manusia, Aku Tak Tertandingi',
    'status': 'pending',
    'addedAt': '2026-06-09T00:51:00Z',
    'processedAt': None
}

existing_ids = [item['id'] for item in queue]
if new_drama['id'] in existing_ids:
    print('Sudah ada di queue!')
else:
    queue.append(new_drama)
    with open(QUEUE_PATH, 'w', encoding='utf-8') as f:
        json.dump(queue, f, indent=2, ensure_ascii=False)
    title = new_drama['title']
    print(f'Ditambahkan: {title}')
    pending = [i for i in queue if i['status'] == 'pending']
    print(f'Total pending sekarang: {len(pending)}')
    for p in pending:
        print(f'  -> {p["title"]}')
