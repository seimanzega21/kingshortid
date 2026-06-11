import requests
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://vidrama.asia/',
    'Cookie': '_fbp=fb.1.1770653154777.876935444165455244; global_ui_lang=id; cf_clearance=gi8rBDL4U_sV5dFUP.Dckjr.DONUzFar9fJlBMJx5_c-1778228148-1.2.1.1-rcSC4qbKF5H0KxB5Zt6Ic88iCIyXH7DESdcJA5w9WLWZvk58Y70clfcHFfqOyxmSRb1I97eRy.96PRr0zF1vV_PWs7vWkLZg2IsJNYLl5ZJvxdv7AnK4pZgxEBspgbrAod7jxce171vMiENcKPDXk_1eVFpBk_P5H8TA07xIBdq5HsL3uPTZKn8BCJv.HufjCR4mRr3DVOGDRagaNcc1CD_VmnRYY6tkanYH9QuDUyPeqreywRNxjb_5tsJVseZjz24po7Gw9o9ZVi3mSl9Ypm88Po1s4zr5n3DfE5R4BCKekPgqBAog2SDMQmDCWQJjMpzKKsJ_iXUHRaincYv9WQ'
}

BASE = 'https://vidrama.asia/api/pine'

# Try pagination
print("=== PAGINATION TEST ===")
all_ids = set()
for page in range(1, 5):
    for size in [20, 50, 100]:
        url = f'{BASE}?action=list&page={page}&size={size}'
        r = requests.get(url, headers=headers, verify=False, timeout=15)
        dramas = r.json().get('dramas', [])
        new_ids = {d['id'] for d in dramas} - all_ids
        print(f'page={page} size={size} -> {len(dramas)} dramas ({len(new_ids)} new)')
        for d in dramas:
            if d['id'] not in all_ids:
                print(f'  + [{d["id"]}] {d["title"]}')
                all_ids.add(d['id'])
        if not dramas:
            break
    if not dramas:
        break

print(f'\nTotal unique dramas found: {len(all_ids)}')

# Try categories - from the screenshot: Penuh aksi, Harem, Pelajar, Misteri, Romansa sehari-hari, Vampir, Era retro, Horor, Aksi, Romansa senior, Dunia tak terbatas, Pekerja kantoran
print("\n=== CATEGORY TEST ===")
categories = ['action', 'harem', 'romance', 'horror', 'mystery', 'vampire', 'school', 'office', 'unlimited', 'senior', 'retro']
for cat in categories:
    url = f'{BASE}?action=list&category={cat}'
    r = requests.get(url, headers=headers, verify=False, timeout=10)
    dramas = r.json().get('dramas', [])
    if dramas:
        new_in_cat = [d for d in dramas if d['id'] not in all_ids]
        print(f'category={cat} -> {len(dramas)} dramas ({len(new_in_cat)} new)')
        for d in new_in_cat:
            print(f'  + [{d["id"]}] {d["title"]}')
            all_ids.add(d['id'])
