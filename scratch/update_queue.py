import json
from pathlib import Path

QUEUE_PATH = Path(r'd:\kingshortid\scripts\reelshort_queue.json')

with open(QUEUE_PATH, 'r', encoding='utf-8') as f:
    queue = json.load(f)

# 1. Tandai semua drama pending saat ini sebagai 'skipped'
skipped = 0
for item in queue:
    if item.get('status') == 'pending':
        item['status'] = 'skipped'
        skipped += 1

print(f'Marked {skipped} dramas as skipped')

# 2. Tambahkan drama baru di akhir queue sebagai 'pending'
new_drama = {
    "id": "69d876c1ee6e6be5e000f14f",
    "title": "[Versi Dub] Demi Putriku, Aku Membunuh Lagi",
    "status": "pending",
    "addedAt": "2026-06-09T00:45:00Z",
    "processedAt": None
}

# Cek apakah sudah ada di queue
existing_ids = [item['id'] for item in queue]
if new_drama['id'] in existing_ids:
    print(f'Drama already in queue: {new_drama["title"]}')
else:
    queue.append(new_drama)
    print(f'Added new drama: {new_drama["title"]} (ID: {new_drama["id"]})')

with open(QUEUE_PATH, 'w', encoding='utf-8') as f:
    json.dump(queue, f, indent=2, ensure_ascii=False)

print('Queue saved successfully.')
print(f'Total items: {len(queue)}')
print(f'Pending: {sum(1 for i in queue if i["status"] == "pending")}')
print(f'Completed: {sum(1 for i in queue if i["status"] == "completed")}')
print(f'Skipped: {sum(1 for i in queue if i["status"] == "skipped")}')
