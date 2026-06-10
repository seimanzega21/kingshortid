import requests
import json
import time
import urllib3

urllib3.disable_warnings()

targets = [
    'Satu Dewa Perang, Tujuh Ratu',
    'Satu Malam, Tak Ada Jalan Keluar',
    'Menikahi Bos Mantanku',
    'Dari Sopir Taksi Menjadi Pelindungnya',
    'Pengantin Curian Jadi Istriku',
    'Menikahi Si Putri Tidur',
    'Pengawal Tak Terkalahkan',
    'Pendekar yang Diremehkan Akhirnya Mengamuk',
    'Mata Keberuntungan',
    'Jadikan Ini Nyata',
    'Semua Menteriku Ingin Membunuhku',
    'Ahli Waris yang Hilang',
    'Pendekar Pedang Terjatuh Kembali',
    'Cinta Seorang Ibu Menemukan Nilainya'
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
                # Some search results don't have provider field or it's None.
                # So we just match the title exactly or closely
                if t.lower() in d.get('title', '').lower():
                    queue.append({
                        'id': d['id'],
                        'title': d['title'],
                        'status': 'pending',
                        'addedAt': '2026-06-10T12:00:00Z',
                        'processedAt': None
                    })
                    print(f"Found: {d['title']} ({d['id']})")
                    found = True
                    break
            if not found:
                print(f"Not found for: {t}")
        time.sleep(1)
    except Exception as e:
        print('Error:', e)

with open('scripts/freereels_queue.json', 'w', encoding='utf-8') as f:
    json.dump(queue, f, indent=2, ensure_ascii=False)
