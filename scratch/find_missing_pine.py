import requests
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://vidrama.asia/',
    'Cookie': '_fbp=fb.1.1770653154777.876935444165455244; global_ui_lang=id; cf_clearance=gi8rBDL4U_sV5dFUP.Dckjr.DONUzFar9fJlBMJx5_c-1778228148-1.2.1.1-rcSC4qbKF5H0KxB5Zt6Ic88iCIyXH7DESdcJA5w9WLWZvk58Y70clfcHFfqOyxmSRb1I97eRy.96PRr0zF1vV_PWs7vWkLZg2IsJNYLl5ZJvxdv7AnK4pZgxEBspgbrAod7jxce171vMiENcKPDXk_1eVFpBk_P5H8TA07xIBdq5HsL3uPTZKn8BCJv.HufjCR4mRr3DVOGDRagaNcc1CD_VmnRYY6tkanYH9QuDUyPeqreywRNxjb_5tsJVseZjz24po7Gw9o9ZVi3mSl9Ypm88Po1s4zr5n3DfE5R4BCKekPgqBAog2SDMQmDCWQJjMpzKKsJ_iXUHRaincYv9WQ'
}

BASE = 'https://vidrama.asia/api/pine'

# Try fetching the provider page to get all IDs
# The page shows 20 dramas with "Penuh aksi" filter active
# Let's try the search with various keywords visible in the screenshot
# and also try different API category params

known_ids = {
    '7633639412135924737',  # Sang Legenda
    '7633627954073015313',  # Cewek Super Bikin Baper
    '7633642976383783953',  # Cinta Pertama Berjuta Rasanya
    '7633697886450095124',  # Mimpi Buruk Keluarga Jutawan
    '7633692990938305552',  # Kekasih Masa Kecil
    '7633277914058118145',  # Maaf Dari Ibu
    '7633641297059976208',  # Berbagi Ayah
    '7633630123840902160',  # Cinta yang Terlupakan
    '7633648292395652097',  # Itik Jadi Angsa
    '7633399236566062081',  # Taman Takdir Cowok Tajir
    '7633270594960086033',  # Makin Ditahan, Makin Penasaran
    '7637081563829916673',  # Dokter sakti dari desa
}

# IDs visible in the screenshot URL bar: 7646413641771176380 (Tiga istri untuk sang prajurit from URL shown)
# Let's check these titles from the screenshot by searching
titles_from_screenshot = [
    'Dendam kesatria terakhir',
    'Master tenis meja tersembunyi',
    'Tiga istri untuk sang prajurit',
    'Dokter Hewan Para Raja Iblis',
    'Relik yang hilang memanggil ibu',
    'Balas dendam sang raja tinju',
    'Dendam Sang Master',
    'Putri sakti jadi peramal',
    'Sang jagoan jalanan',
    'Evolusi ular pemangsa',
    'Sang Raja Dewa',
    'Kebangkitan Raja Kera',
    'Sang juara menyamar jadi OB',
    'Suamiku sang Raja Asura',
]

print("=== SEARCHING FOR NEW DRAMAS ===")
new_dramas = []
for title in titles_from_screenshot:
    # Use first 3 words for search
    words = title.split()[:3]
    query = ' '.join(words)
    r = requests.get(f'{BASE}?action=search&keyword={query}', headers=headers, verify=False, timeout=10)
    if r.ok:
        dramas = r.json().get('dramas', [])
        for d in dramas:
            if d['id'] not in known_ids:
                # Check if title is similar
                if any(w.lower() in d['title'].lower() for w in words):
                    print(f'  FOUND: [{d["id"]}] {d["title"]} (search: {query})')
                    known_ids.add(d['id'])
                    new_dramas.append(d)

print(f'\nNew dramas found: {len(new_dramas)}')
print('\nAll new drama IDs:')
for d in new_dramas:
    print(f'  "{d["id"]}",  # {d["title"]}')
