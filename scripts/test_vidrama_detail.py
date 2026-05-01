import requests, json, urllib3
urllib3.disable_warnings()

VIDRAMA_API = 'https://vidrama.asia/api/netshortv2'
WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
    'Cookie': '_fbp=fb.1.1770653154777.876935444165455244; _tt_enable_cookie=1; _ttp=01KH1JE0K4H648BY6E3FQ6EXRZ_.tt.1; _ga=GA1.1.1826262121.1771037718; HstCfa5004644=1772873251576; c_ref_5004644=https%3A%2F%2Fwww.google.com%2F; __dtsu=4C301774685394D291D3AB624E4AA57E; _pubcid=8a5abbf9-164b-422f-b349-0e1ba702ea69; _cc_id=a4a99f9a552125d19ea447bfafb9c63b; HstCmu5004644=1776164034743; HstPn5004644=1; cf_clearance=AQRjv4.Cj2nHbg_KLivmkViGOllnwGPpIVkj35_jfKI-1777471778-1.2.1.1-TEdhFr7wBXOwe6l8ybhNx3V3OAO2FmEP81fCwLc_mclcsLHuLye6b0vcwrShIGHIdgmlaY14VoOLGlccyUA11WHrRIEncihkGDwdc8C44c79F_3U4SEVsPeQAtPP.1_v6j.daxeE5gMBUPycNwj8rIn4fxg5dhhxrCsZvPIyDKo0BUWtkSEcjfRXcll7MrK8y3YSM8WhGmqI.PzKcfsFF.006ENmy7BGlLwqjy_QDYg8Y7xuxVKlIr_3ApmsnXItGKvJ2DDt_XQUqh1H5hqKnf50BS4QFNfxQEUeytk94ofP8SYQwlqg1HEIz3BMlJC4OQhzn5m0L6muYtASD.jwaw; HstCla5004644=1777471778959; HstPt5004644=72; HstCnv5004644=31; HstCns5004644=35; panoramaId_expiry=1777558180696; _ga_HCQQPKGEVH=GS2.1.s1777476684$o70$g1$t1777477281$j55$l0$h0; ttcsid_D5SNQPRC77UDQTF8A5EG=1777476683162::JiaNdPsba2GCy8oVLuyE.75.1777477294114.1; ttcsid=1777476683155::c9Pa9Oee_DaSEml_Mj5I.85.1777477294114.0::1.610918.6485::610880.63.113.1122::610008.512.600'
}

DRAMA_ID = '2009874568801701890'

# Get detail
url = f"{VIDRAMA_API}/detail/{DRAMA_ID}?lang=id_ID"
r = requests.get(url, headers=WEB_HDRS, timeout=15, verify=False)
data = r.json()

print('=== VIDRAMA DETAIL ===')
print(f"Status code: {data.get('code')}")
print(f"Message: {data.get('message')}")
d = data.get('data', {})
print(f"Title: {d.get('title')}")
print(f"Total Episodes: {d.get('totalEpisodes')}")
print(f"Is Finished: {d.get('isFinished')}")
print(f"Cover: {str(d.get('cover', ''))[:100]}")
print(f"Description (first 200 chars): {str(d.get('description', ''))[:200]}")
print(f"Labels: {d.get('labels')}")
eps = d.get('episodes', [])
print(f"Episodes count in list: {len(eps)}")
if eps:
    print(f"First 5 episode numbers: {[ep.get('episodeNo') for ep in eps[:5]]}")
    print(f"Last 5 episode numbers: {[ep.get('episodeNo') for ep in eps[-5:]]}")

# Test episode 1 URL
print()
print('=== EPISODE 1 URL TEST ===')
ep_url = f"{VIDRAMA_API}/episode/{DRAMA_ID}/1?lang=id_ID"
ep_r = requests.get(ep_url, headers=WEB_HDRS, timeout=15, verify=False)
ep_data = ep_r.json()
print(f"Status: {ep_data.get('code')}")
ep_d = ep_data.get('data', {})
videos = ep_d.get('videos', [])
print(f"Videos count: {len(videos)}")
for v in videos[:3]:
    print(f"  Quality: {v.get('quality')}, URL: {str(v.get('url', ''))[:80]}...")
print(f"Subtitles count: {len(ep_d.get('subtitles', []))}")
print(f"Episode ID: {ep_d.get('episodeId')}")

# Test episode 2 URL
print()
print('=== EPISODE 2 URL TEST ===')
ep_url2 = f"{VIDRAMA_API}/episode/{DRAMA_ID}/2?lang=id_ID"
ep_r2 = requests.get(ep_url2, headers=WEB_HDRS, timeout=15, verify=False)
ep_data2 = ep_r2.json()
print(f"Status: {ep_data2.get('code')}")
if ep_data2.get('code') == 200:
    ep_d2 = ep_data2.get('data', {})
    videos2 = ep_d2.get('videos', [])
    print(f"Videos count: {len(videos2)}")
    for v in videos2[:2]:
        print(f"  Quality: {v.get('quality')}, URL: {str(v.get('url', ''))[:80]}...")
else:
    print(f"Error: {ep_data2.get('message')}")
    print(f"Full response: {ep_data2}")
