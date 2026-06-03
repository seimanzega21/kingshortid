import requests
import json
import urllib3

urllib3.disable_warnings()

API_BASE = 'https://api.shortlovers.id'
ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

DRAMA_ID = 'pjr00rw58d0y73bk7axn1buy'
BOOK_ID = '42000007062'

print("=== CHECKING SYSTEM EPISODES ===")
# 1. Fetch episodes from our database
url = f"{API_BASE}/api/dramas/{DRAMA_ID}/episodes?includeInactive=true"
r = requests.get(url, headers=ADMIN_HDR, timeout=15)
if r.ok:
    eps = r.json()
    ep_list = eps if isinstance(eps, list) else eps.get('episodes', eps.get('data', []))
    print(f"Total episodes in our database: {len(ep_list)}")
    our_ep_nums = sorted([e.get('episodeNumber') for e in ep_list])
    print("Our episodes:", our_ep_nums)
else:
    print(f"Failed to fetch our episodes: {r.status_code} - {r.text}")
    our_ep_nums = []

# 2. Fetch drama metadata from Vidrama Dramabox3 API
print("\n=== CHECKING PROVIDER METADATA ===")
provider_url = f"https://vidrama.asia/api/dramabox3/drama/{BOOK_ID}?lang=in"
COOKIE = '_fbp=fb.1.1770653154777.876935444165455244; _tt_enable_cookie=1; _ttp=01KH1JE0K4H648BY6E3FQ6EXRZ_.tt.1; _ga=GA1.1.1826262121.1771037718; HstCfa5004644=1772873251576; c_ref_5004644=https%3A%2F%2Fwww.google.com%2F; __dtsu=4C301774685394D291D3AB624E4AA57E; _pubcid=8a5abbf9-164b-422f-b349-0e1ba702ea69; _cc_id=a4a99f9a552125d19ea447bfafb9c63b; global_ui_lang=id; HstCmu5004644=1779384259258; vidrama_chat_anon=45cc06417e3a261dc8f368a8; HstCnv5004644=48; cf_clearance=N5A.kyHMnJ7RBK3hOyqybB6KddOTpRsZyEiE.fgp5kM-1779713242-1.2.1.1-9YHMfsNOniF6J54T1_JEaJY6mYbVJWOz8Kkm0raJacrpotGOYzyN_gG.Kxb7kfPxOO1wYdSenqFW0HIUwqQ57F5gqyjRbwvS8_r8rLFxIbYHNWMAahrr.iKy0dsa1krg8mVhzXDilHK71X.Iszvd8uo_CwVzbHiVUurJ8eF1DyguF2fK1vFa68H3Z5HFzZhBvVaIle1tEW3443.tH9TYjQX.7HKB9SBI2ZHkNto2vDQ2F77XP3cLmCp7GPXINCG8mrZf6l5xsxuh_xyqNp1bIRyxkUhz9IooxQKp3yV9Crri9TFW9II5q0M50yOlhCROGsKwa0AkIkKtWi.pNc5ATg; HstCla5004644=1779713242621; HstPn5004644=2; HstPt5004644=93; HstCns5004644=54; panoramaId_expiry=1779799644224'

VIDRAMA_HDR = {
    'accept': '*/*',
    'accept-language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
    'cookie': COOKIE,
    'priority': 'u=1, i',
    'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Mobile Safari/537.36'
}

r_prov = requests.get(provider_url, headers=VIDRAMA_HDR, verify=False)
if r_prov.ok:
    data = r_prov.json()
    d = data.get('data', {})
    print(f"Book Name: {d.get('bookName')}")
    print(f"Chapter Count: {d.get('chapterCount')}")
    print(f"Book Status: {d.get('bookStatus')} (1=ongoing, 2=completed)")
    
    total_chapters = d.get('chapterCount', 0)
    # Check which episodes are missing
    missing_eps = []
    for i in range(1, total_chapters + 1):
        if i not in our_ep_nums:
            missing_eps.append(i)
    print(f"\nMissing episodes to scrape: {missing_eps}")
else:
    print(f"Failed to fetch provider metadata: {r_prov.status_code} - {r_prov.text}")
