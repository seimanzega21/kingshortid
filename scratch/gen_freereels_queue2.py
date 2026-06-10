import requests
import json
import time
import urllib3

urllib3.disable_warnings()

targets = [
    'Satu Dewa Perang',
    'Tak Ada Jalan Keluar',
    'Menikahi Bos Mantanku',
    'Dari Sopir Taksi',
    'Pengantin Curian',
    'Si Putri Tidur',
    'Pengawal Tak Terkalahkan',
    'Pendekar yang Diremehkan',
    'Mata Keberuntungan',
    'Jadikan Ini Nyata',
    'Menteriku Ingin Membunuhku',
    'Ahli Waris yang Hilang',
    'Pendekar Pedang Terjatuh',
    'Cinta Seorang Ibu'
]

queue = []

for t in targets:
    url = f'https://vidrama.asia/api/search/global?q={t}'
    try:
        r = requests.get(url, verify=False, timeout=10)
        if r.ok:
            data = r.json().get('data', [])
            found = False
            for d in data:
                vid_id = d.get('id', '')
                if len(vid_id) == 10 and vid_id.isalnum():
                    queue.append({
                        'id': vid_id,
                        'title': d['title'],
                        'status': 'pending',
                        'addedAt': '2026-06-10T12:00:00Z',
                        'processedAt': None
                    })
                    print(f"Found: {d['title']} ({vid_id})")
                    found = True
                    break
            if not found:
                print(f"Not found for: {t}")
        time.sleep(1)
    except Exception as e:
        print('Error:', e)

with open('scripts/freereels_queue.json', 'w', encoding='utf-8') as f:
    json.dump(queue, f, indent=2, ensure_ascii=False)
