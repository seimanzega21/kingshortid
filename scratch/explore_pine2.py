import requests
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://vidrama.asia/',
    'Cookie': '_fbp=fb.1.1770653154777.876935444165455244; global_ui_lang=id; cf_clearance=gi8rBDL4U_sV5dFUP.Dckjr.DONUzFar9fJlBMJx5_c-1778228148-1.2.1.1-rcSC4qbKF5H0KxB5Zt6Ic88iCIyXH7DESdcJA5w9WLWZvk58Y70clfcHFfqOyxmSRb1I97eRy.96PRr0zF1vV_PWs7vWkLZg2IsJNYLl5ZJvxdv7AnK4pZgxEBspgbrAod7jxce171vMiENcKPDXk_1eVFpBk_P5H8TA07xIBdq5HsL3uPTZKn8BCJv.HufjCR4mRr3DVOGDRagaNcc1CD_VmnRYY6tkanYH9QuDUyPeqreywRNxjb_5tsJVseZjz24po7Gw9o9ZVi3mSl9Ypm88Po1s4zr5n3DfE5R4BCKekPgqBAog2SDMQmDCWQJjMpzKKsJ_iXUHRaincYv9WQ'
}

BASE = 'https://vidrama.asia/api/pine'

# 1. Get full list
print("=== LIST (page/size params) ===")
for page in [1, 2]:
    for size in [50, 100]:
        url = f'{BASE}?action=list&page={page}&size={size}'
        r = requests.get(url, headers=headers, verify=False, timeout=10)
        data = r.json()
        dramas = data.get('dramas', [])
        print(f'page={page} size={size} -> {len(dramas)} dramas')
        if page == 1 and size == 50 and dramas:
            for d in dramas[:5]:
                print(f'  - [{d["id"]}] {d["title"]}')
        if dramas:
            break
    if dramas:
        break

print()

# 2. Get detail with collection_id
first_id = dramas[0]['id'] if dramas else '7643677444247311367'
print(f"=== DETAIL (collection_id={first_id}) ===")
detail_tests = [
    f'action=detail&collection_id={first_id}',
    f'action=detail&collection_id={first_id}&lang=id',
    f'action=detail&collection_id={first_id}&lang=id_ID',
]
for params in detail_tests:
    r = requests.get(f'{BASE}?{params}', headers=headers, verify=False, timeout=10)
    print(f'[{r.status_code}] {params}')
    print(f'  -> {r.text[:400]}')
    print()
