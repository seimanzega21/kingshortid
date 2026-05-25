# -*- coding: utf-8 -*-
import requests, json, urllib3, sys
urllib3.disable_warnings()

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

VIDRAMA_API = 'https://vidrama.asia/api/dramabox3'
WEB_HDRS = {
  'accept': '*/*',
  'accept-language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
  'cookie': '_fbp=fb.1.1770653154777.876935444165455244; _tt_enable_cookie=1; _ttp=01KH1JE0K4H648BY6E3FQ6EXRZ_.tt.1; _ga=GA1.1.1826262121.1771037718; HstCfa5004644=1772873251576; c_ref_5004644=https%3A%2F%2Fwww.google.com%2F; __dtsu=4C301774685394D291D3AB624E4AA57E; _pubcid=8a5abbf9-164b-422f-b349-0e1ba702ea69; _cc_id=a4a99f9a552125d19ea447bfafb9c63b; global_ui_lang=id; HstCmu5004644=1779384259258; vidrama_chat_anon=45cc06417e3a261dc8f368a8; HstCnv5004644=48; cf_clearance=N5A.kyHMnJ7RBK3hOyqybB6KddOTpRsZyEiE.fgp5kM-1779713242-1.2.1.1-9YHMfsNOniF6J54T1_JEaJY6mYbVJWOz8Kkm0raJacrpotGOYzyN_gG.Kxb7kfPxOO1wYdSenqFW0HIUwqQ57F5gqyjRbwvS8_r8rLFxIbYHNWMAahrr.iKy0dsa1krg8mVhzXDilHK71X.Iszvd8uo_CwVzbHiVUurJ8eF1DyguF2fK1vFa68H3Z5HFzZhBvVaIle1tEW3443.tH9TYjQX.7HKB9SBI2ZHkNto2vDQ2F77XP3cLmCp7GPXINCG8mrZf6l5xsxuh_xyqNp1bIRyxkUhz9IooxQKp3yV9Crri9TFW9II5q0M50yOlhCROGsKwa0AkIkKtWi.pNc5ATg; HstCla5004644=1779713242621; HstPn5004644=2; HstPt5004644=93; HstCns5004644=54; panoramaId_expiry=1779799644224; _ga_HCQQPKGEVH=GS2.1.s1779711231$o100$g1$t1779713484$j15$l0$h0; ttcsid_D5SNQPRC77UDQTF8A5EG=1779711232314::DPPuPq1KuyT3L7DbqDo-.101.1779713495346.1; ttcsid=1779711232315::UpgCYs8WSRhaxtiwxmvM.119.1779713495346.0::1.2262997.2010795::2262959.43.72.1199::2261551.112.500',
  'priority': 'u=1, i',
  'referer': 'https://vidrama.asia/watch/menjebak-di-dalam-jebakan--42000009069/1?provider=dramabox3&lang=in',
  'sec-ch-ua': '"Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"',
  'sec-ch-ua-mobile': '?1',
  'sec-ch-ua-platform': '"Android"',
  'sec-fetch-dest': 'empty',
  'sec-fetch-mode': 'cors',
  'sec-fetch-site': 'same-origin',
  'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Mobile Safari/537.36'
}

DRAMA_ID = '42000009069'

# Get detail
url = f"{VIDRAMA_API}/watch?bookId={DRAMA_ID}&episode=1&lang=in"
r = requests.get(url, headers=WEB_HDRS, timeout=15, verify=False)
data = r.json()

print("=== VIDRAMA DETAIL ===")
print(f"Status: {data.get('code')}")
print(f"Message: {data.get('message')}")
d = data.get('data', {})
if d:
    print(f"Title: {d.get('title')}")
    print(f"Total Episodes: {d.get('totalEpisodes')}")
    print(f"Is Finished: {d.get('isFinished')}")
    print(f"Cover: {d.get('cover')}")
    print(f"Description (first 200 chars): {str(d.get('description', ''))[:200]}")
    print(f"Labels: {d.get('labels')}")
    print(f"Episodes count in list: {len(d.get('episodes', []))}")
    print(f"First 5 episode numbers: {[ep.get('episodeNo') for ep in d.get('episodes', [])[:5]]}")
    print(f"Last 5 episode numbers: {[ep.get('episodeNo') for ep in d.get('episodes', [])[-5:]]}")
else:
    print("No data in detail response")

# Test episode 1 URL
print("\n=== EPISODE 1 URL TEST ===")
ep_url = f"{VIDRAMA_API}/episode/{DRAMA_ID}/1?lang=id_ID"
ep_r = requests.get(ep_url, headers=WEB_HDRS, timeout=15, verify=False)
ep_data = ep_r.json()
print(f"Status: {ep_data.get('code')}")
ep_d = ep_data.get('data', {})
videos = ep_d.get('videos', [])
print(f"Videos count: {len(videos)}")
for v in videos[:3]:
    print(f"  Quality: {v.get('quality')}, URL: {str(v.get('url', ''))[:80]}...")
print(f"Subtitles: {ep_d.get('subtitles')}")
print(f"Episode ID: {ep_d.get('episodeId')}")

# Test episode 2 URL
print("\n=== EPISODE 2 URL TEST ===")
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
