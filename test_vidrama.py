import requests, json, urllib3, re
urllib3.disable_warnings()

VIDRAMA_API = 'https://vidrama.asia/api/netshortv2'
WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
    'Cookie': '_fbp=fb.1.1770653154777.876935444165455244; _tt_enable_cookie=1; _ttp=01KH1JE0K4H648BY6E3FQ6EXRZ_.tt.1; _ga=GA1.1.1826262121.1771037718; HstCfa5004644=1772873251576; c_ref_5004644=https%3A%2F%2Fwww.google.com%2F; __dtsu=4C301774685394D291D3AB624E4AA57E; _pubcid=8a5abbf9-164b-422f-b349-0e1ba702ea69; _cc_id=a4a99f9a552125d19ea447bfafb9c63b; HstCmu5004644=1776164034743; HstPn5004644=1; cf_clearance=AQRjv4.Cj2nHbg_KLivmkViGOllnwGPpIVkj35_jfKI-1777471778-1.2.1.1-TEdhFr7wBXOwe6l8ybhNx3V3OAO2FmEP81fCwLc_mclcsLHuLye6b0vcwrShIGHIdgmlaY14VoOLGlccyUA11WHrRIEncihkGDwdc8C44c79F_3U4SEVsPeQAtPP.1_v6j.daxeE5gMBUPycNwj8rIn4fxg5dhhxrCsZvPIyDKo0BUWtkSEcjfRXcll7MrK8y3YSM8WhGmqI.PzKcfsFF.006ENmy7BGlLwqjy_QDYg8Y7xuxVKlIr_3ApmsnXItGKvJ2DDt_XQUqh1H5hqKnf50BS4QFNfxQEUeytk94ofP8SYQwlqg1HEIz3BMlJC4OQhzn5m0L6muYtASD.jwaw; HstCla5004644=1777471778959; HstPt5004644=72; HstCnv5004644=31; HstCns5004644=35; panoramaId_expiry=1777558180696; _ga_HCQQPKGEVH=GS2.1.s1777476684$o70$g1$t1777477281$j55$l0$h0; ttcsid_D5SNQPRC77UDQTF8A5EG=1777476683162::JiaNdPsba2GCy8oVLuyE.75.1777477294114.1; ttcsid=1777476683155::c9Pa9Oee_DaSEml_Mj5I.85.1777477294114.0::1.610918.6485::610880.63.113.1122::610008.512.600'
}

# 1. Test discovery API
print("=== TEST 1: DISCOVERY API ===")
for page in range(1, 5):
    url = f"{VIDRAMA_API}/feed/{page}?lang=id_ID"
    try:
        r = requests.get(url, headers=WEB_HDRS, timeout=15, verify=False)
        print(f"Page {page}: status={r.status_code}")
        if r.ok:
            data = r.json()
            items = data.get('data', [])
            print(f"  Items: {len(items)}")
            for it in items[:3]:
                title = it.get('title', '')
                drama_id = it.get('id', '')
                print(f"    - {title} (ID: {drama_id})")
                if 'pewaris' in title.lower() or 'perjuangan' in title.lower():
                    print(f"    >>> FOUND TARGET: {title} ID={drama_id}")
    except Exception as e:
        print(f"Page {page}: ERROR {e}")

# 2. If found, test detail API
print("\n=== TEST 2: SEARCH BY TITLE ===")
# Also try searching with different terms
search_terms = ['perjuangan', 'pewaris', 'sejati']
for page in range(1, 10):
    url = f"{VIDRAMA_API}/feed/{page}?lang=id_ID"
    try:
        r = requests.get(url, headers=WEB_HDRS, timeout=15, verify=False)
        if r.ok:
            items = r.json().get('data', [])
            for it in items:
                title = it.get('title', '').lower()
                if any(term in title for term in search_terms):
                    drama_id = it.get('id', '')
                    print(f"MATCH: {it.get('title')} | ID: {drama_id}")
    except: pass

print("\nDone")
