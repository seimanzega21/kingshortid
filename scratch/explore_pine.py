import requests
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://vidrama.asia/',
    'Cookie': '_fbp=fb.1.1770653154777.876935444165455244; global_ui_lang=id; cf_clearance=gi8rBDL4U_sV5dFUP.Dckjr.DONUzFar9fJlBMJx5_c-1778228148-1.2.1.1-rcSC4qbKF5H0KxB5Zt6Ic88iCIyXH7DESdcJA5w9WLWZvk58Y70clfcHFfqOyxmSRb1I97eRy.96PRr0zF1vV_PWs7vWkLZg2IsJNYLl5ZJvxdv7AnK4pZgxEBspgbrAod7jxce171vMiENcKPDXk_1eVFpBk_P5H8TA07xIBdq5HsL3uPTZKn8BCJv.HufjCR4mRr3DVOGDRagaNcc1CD_VmnRYY6tkanYH9QuDUyPeqreywRNxjb_5tsJVseZjz24po7Gw9o9ZVi3mSl9Ypm88Po1s4zr5n3DfE5R4BCKekPgqBAog2SDMQmDCWQJjMpzKKsJ_iXUHRaincYv9WQ'
}

tests = [
    'action=detail&id=7643677444247311367',
    'action=detail&seriesId=7643677444247311367',
    'action=series&id=7643677444247311367',
    'action=info&id=7643677444247311367',
    'action=home',
    'action=list',
    'action=search&keyword=cinta',
    'action=category',
    'action=recommend',
]

for params in tests:
    url = 'https://vidrama.asia/api/pine?' + params
    try:
        r = requests.get(url, headers=headers, verify=False, timeout=10)
        txt = r.text[:300]
        print(f'[{r.status_code}] {params}')
        print(f'  -> {txt}')
        print()
    except Exception as e:
        print(f'[ERR] {params}: {e}')
