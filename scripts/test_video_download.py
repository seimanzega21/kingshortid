import requests, urllib3
urllib3.disable_warnings()

VIDRAMA_API = 'https://vidrama.asia/api/netshortv2'
WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
    'Cookie': '_fbp=fb.1.1770653154777.876935444165455244; _tt_enable_cookie=1; _ttp=01KH1JE0K4H648BY6E3FQ6EXRZ_.tt.1; _ga=GA1.1.1826262121.1771037718; HstCfa5004644=1772873251576; c_ref_5004644=https%3A%2F%2Fwww.google.com%2F; __dtsu=4C301774685394D291D3AB624E4AA57E; _pubcid=8a5abbf9-164b-422f-b349-0e1ba702ea69; _cc_id=a4a99f9a552125d19ea447bfafb9c63b; HstCmu5004644=1776164034743; HstPn5004644=1; cf_clearance=AQRjv4.Cj2nHbg_KLivmkViGOllnwGPpIVkj35_jfKI-1777471778-1.2.1.1-TEdhFr7wBXOwe6l8ybhNx3V3OAO2FmEP81fCwLc_mclcsLHuLye6b0vcwrShIGHIdgmlaY14VoOLGlccyUA11WHrRIEncihkGDwdc8C44c79F_3U4SEVsPeQAtPP.1_v6j.daxeE5gMBUPycNwj8rIn4fxg5dhhxrCsZvPIyDKo0BUWtkSEcjfRXcll7MrK8y3YSM8WhGmqI.PzKcfsFF.006ENmy7BGlLwqjy_QDYg8Y7xuxVKlIr_3ApmsnXItGKvJ2DDt_XQUqh1H5hqKnf50BS4QFNfxQEUeytk94ofP8SYQwlqg1HEIz3BMlJC4OQhzn5m0L6muYtASD.jwaw; HstCla5004644=1777471778959; HstPt5004644=72; HstCnv5004644=31; HstCns5004644=35; panoramaId_expiry=1777558180696; _ga_HCQQPKGEVH=GS2.1.s1777476684$o70$g1$t1777477281$j55$l0$h0; ttcsid_D5SNQPRC77UDQTF8A5EG=1777476683162::JiaNdPsba2GCy8oVLuyE.75.1777477294114.1; ttcsid=1777476683155::c9Pa9Oee_DaSEml_Mj5I.85.1777477294114.0::1.610918.6485::610880.63.113.1122::610008.512.600'
}

DRAMA_ID = '2009874568801701890'

# Get episode 1 URL fresh
print('=== GET EPISODE 1 URL FROM API ===')
ep_url = f"{VIDRAMA_API}/episode/{DRAMA_ID}/1?lang=id_ID"
ep_r = requests.get(ep_url, headers=WEB_HDRS, timeout=15, verify=False)
ep_data = ep_r.json()
print(f"API Status: {ep_data.get('code')}")

if ep_data.get('code') == 200:
    ep_d = ep_data.get('data', {})
    videos = ep_d.get('videos', [])
    best_url = None
    for q in ['720p', '1080p', '540p']:
        for v in videos:
            if v.get('quality') == q:
                best_url = v['url']
                break
        if best_url: break
    
    if best_url:
        print(f"Best URL ({q}): {best_url}")
        
        # Test HEAD
        print()
        print('=== TEST VIDEO URL HEAD ===')
        r = requests.head(best_url, timeout=10, verify=False, allow_redirects=True)
        print(f"HEAD status: {r.status_code}")
        print(f"Content-Type: {r.headers.get('Content-Type')}")
        
        # Test partial download
        print()
        print('=== TEST PARTIAL DOWNLOAD ===')
        r2 = requests.get(best_url, stream=True, timeout=15, verify=False)
        print(f"GET status: {r2.status_code}")
        print(f"Content-Type: {r2.headers.get('Content-Type')}")
        
        total = 0
        for chunk in r2.iter_content(1024*1024):
            total += len(chunk)
            if total >= 2*1024*1024:
                break
        print(f"Downloaded: {total} bytes (2MB test)")
        print("SUCCESS: Video URL is accessible!")
    else:
        print("No video URL found!")
else:
    print(f"Failed: {ep_data}")
