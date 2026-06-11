import requests
import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://vidrama.asia/',
    'Cookie': '_fbp=fb.1.1770653154777.876935444165455244; global_ui_lang=id; cf_clearance=gi8rBDL4U_sV5dFUP.Dckjr.DONUzFar9fJlBMJx5_c-1778228148-1.2.1.1-rcSC4qbKF5H0KxB5Zt6Ic88iCIyXH7DESdcJA5w9WLWZvk58Y70clfcHFfqOyxmSRb1I97eRy.96PRr0zF1vV_PWs7vWkLZg2IsJNYLl5ZJvxdv7AnK4pZgxEBspgbrAod7jxce171vMiENcKPDXk_1eVFpBk_P5H8TA07xIBdq5HsL3uPTZKn8BCJv.HufjCR4mRr3DVOGDRagaNcc1CD_VmnRYY6tkanYH9QuDUyPeqreywRNxjb_5tsJVseZjz24po7Gw9o9ZVi3mSl9Ypm88Po1s4zr5n3DfE5R4BCKekPgqBAog2SDMQmDCWQJjMpzKKsJ_iXUHRaincYv9WQ'
}

PINE_API = 'https://vidrama.asia/api/pine'

# URLs from user
urls = [
    'https://vidrama.asia/movie/dendam-kesatria-terakhir--7646413653666911250?provider=pine&lang=id',
    'https://vidrama.asia/movie/master-tenis-meja-tersembunyi--7646964476893402132?provider=pine&lang=id&region=ID',
    'https://vidrama.asia/movie/dewa-pembunuh-di-tahap-qi--7644896821504201749?provider=pine&lang=id&region=ID',
    'https://vidrama.asia/movie/istriku-ternyata-kaisar-wanita--7647030977172329493?provider=pine&lang=id',
    'https://vidrama.asia/movie/satpam-jadi-master-dadakan--7646458746113364993?provider=pine&lang=id&region=ID',
    'https://vidrama.asia/movie/ayahku-sang-juara-tersembunyi--7638977329955984405?provider=pine&lang=id&region=ID',
    'https://vidrama.asia/movie/tiga-istri-untuk-sang-prajurit--7646413641771717639?provider=pine&lang=id&region=ID',
    'https://vidrama.asia/movie/suami-kontrak-sang-putri--7644855730528785428?provider=pine&lang=id&region=ID',
    'https://vidrama.asia/movie/dokter-hewan-para-raja-iblis--7647572433456698376?provider=pine&lang=id&region=ID',
    'https://vidrama.asia/movie/sang-legenda-yang-kembali--7605896042286470152?provider=pine&lang=id&region=ID',
    'https://vidrama.asia/movie/relik-yang-hilang-memanggilnya-ibu--7614764460615455761?provider=pine&lang=id&region=ID',
    'https://vidrama.asia/movie/suamiku-sang-raja-asura--7647102810487542801?provider=pine&lang=id&region=ID',
    'https://vidrama.asia/movie/balas-dendam-sang-raja-tinju--7645639160547578900?provider=pine&lang=id&region=ID',
    'https://vidrama.asia/movie/sang-juara-menyamar-jadi-ob--7643677444247311367?provider=pine&lang=id&region=ID',
    'https://vidrama.asia/movie/dendam-sang-master--7647659566897304596?provider=pine&lang=id&region=ID',
    'https://vidrama.asia/movie/putri-sakti-jadi-peramal--7646377567255172117?provider=pine&lang=id&region=ID',
    'https://vidrama.asia/movie/sang-jagoan-jalanan--7647221148912096257?provider=pine&lang=id&region=ID',
    'https://vidrama.asia/movie/evolusi-ular-pemangsa--7646731532383900692?provider=pine&lang=id&region=ID',
    'https://vidrama.asia/movie/sang-raja-dewa--7647097496782869524?provider=pine&lang=id&region=ID',
    'https://vidrama.asia/movie/kebangkitan-raja-kera--7647012114024371221?provider=pine&lang=id&region=ID',
]

# IDs already being processed by current scraper (the 12 from action=list)
already_processing = {
    '7633639412135924737', '7633627954073015313', '7633642976383783953',
    '7633697886450095124', '7633692990938305552', '7633277914058118145',
    '7633641297059976208', '7633630123840902160', '7633648292395652097',
    '7633399236566062081', '7633270594960086033', '7637081563829916673',
}

print("=== VERIFYING 20 DRAMA IDs FROM USER ===\n")
queue = []

for i, url in enumerate(urls, 1):
    # Extract ID from URL
    match = re.search(r'--(\d{16,19})\?', url)
    if not match:
        print(f"{i}. ERROR: Could not extract ID from {url}")
        continue
    
    collection_id = match.group(1)
    slug = url.split('/movie/')[1].split('--')[0]
    
    # Skip if already in current scraper queue
    if collection_id in already_processing:
        print(f"{i}. [SKIP - already in queue] {slug}")
        continue
    
    # Verify via Pine API
    r = requests.get(f'{PINE_API}?action=detail&collection_id={collection_id}',
                     headers=headers, verify=False, timeout=15)
    if r.ok and r.json().get('title'):
        data = r.json()
        title = data['title']
        total_eps = data.get('totalEpisodes', 0)
        print(f"{i}. OK -> [{collection_id}] {title} ({total_eps} ep)")
        queue.append({
            'id': collection_id,
            'title': title,
            'totalEpisodes': total_eps,
            'status': 'pending'
        })
    else:
        print(f"{i}. ERROR -> [{collection_id}] HTTP {r.status_code}: {r.text[:100]}")

print(f"\n=== RESULT ===")
print(f"Total verified dramas ready to scrape: {len(queue)}")
for d in queue:
    print(f"  - {d['title']} ({d['totalEpisodes']} ep)")

# Save to pine_queue.json
with open('scripts/pine_queue.json', 'w', encoding='utf-8') as f:
    json.dump(queue, f, ensure_ascii=False, indent=2)

print(f"\nSaved to scripts/pine_queue.json")
