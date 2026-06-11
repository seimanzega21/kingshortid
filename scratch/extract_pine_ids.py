import requests
import re
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
    'Accept-Language': 'id-ID,id;q=0.9,en;q=0.8',
    'Cookie': '_fbp=fb.1.1770653154777.876935444165455244; global_ui_lang=id; cf_clearance=gi8rBDL4U_sV5dFUP.Dckjr.DONUzFar9fJlBMJx5_c-1778228148-1.2.1.1-rcSC4qbKF5H0KxB5Zt6Ic88iCIyXH7DESdcJA5w9WLWZvk58Y70clfcHFfqOyxmSRb1I97eRy.96PRr0zF1vV_PWs7vWkLZg2IsJNYLl5ZJvxdv7AnK4pZgxEBspgbrAod7jxce171vMiENcKPDXk_1eVFpBk_P5H8TA07xIBdq5HsL3uPTZKn8BCJv.HufjCR4mRr3DVOGDRagaNcc1CD_VmnRYY6tkanYH9QuDUyPeqreywRNxjb_5tsJVseZjz24po7Gw9o9ZVi3mSl9Ypm88Po1s4zr5n3DfE5R4BCKekPgqBAog2SDMQmDCWQJjMpzKKsJ_iXUHRaincYv9WQ'
}

PINE_API = 'https://vidrama.asia/api/pine'

# Known IDs already in our list
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

# Fetch the provider page HTML to extract drama IDs
print("Fetching Pine provider page HTML...")
r = requests.get('https://vidrama.asia/provider/pine', headers=headers, verify=False, timeout=30)
print(f"Status: {r.status_code}")

# Extract all numeric IDs that look like TikTok content IDs (16-19 digits)
ids_in_html = set(re.findall(r'"?(\d{16,19})"?', r.text))
print(f"Found {len(ids_in_html)} potential IDs in HTML")

# Extract drama slugs and IDs from href patterns
slug_ids = re.findall(r'/movie/([^"]+?)--(\d{16,19})\?provider=pine', r.text)
print(f"\nDramas found in HTML with provider=pine:")
new_dramas = []
for slug, did in slug_ids:
    if did not in known_ids:
        title_guess = slug.replace('-', ' ').title()
        print(f"  + [{did}] {slug}")
        new_dramas.append(did)
        known_ids.add(did)

print(f"\nTotal new IDs from HTML: {len(new_dramas)}")

# Now verify each new ID against Pine API and get proper title
print("\nVerifying and getting proper titles...")
verified = []
for did in new_dramas[:30]:  # first 30
    r2 = requests.get(f'{PINE_API}?action=detail&collection_id={did}', headers=headers, verify=False, timeout=10)
    if r2.ok:
        data = r2.json()
        title = data.get('title', 'N/A')
        total_eps = data.get('totalEpisodes', '?')
        print(f"  [{did}] {title} ({total_eps} ep)")
        verified.append({'id': did, 'title': title, 'totalEpisodes': total_eps})
    else:
        print(f"  [{did}] ERROR: {r2.status_code}")

print(f"\n=== SUMMARY ===")
print(f"Verified new dramas: {len(verified)}")
for d in verified:
    did = d['id']
    title = d['title']
    eps = d['totalEpisodes']
    print(f'  "{did}",  # {title} ({eps} ep)')
