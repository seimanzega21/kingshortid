import requests
import urllib3
urllib3.disable_warnings()

COOKIE = '_fbp=fb.1.1770653154777.876935444165455244; _tt_enable_cookie=1; _ttp=01KH1JE0K4H648BY6E3FQ6EXRZ_.tt.1; _ga=GA1.1.1826262121.1771037718; HstCfa5004644=1772873251576; c_ref_5004644=https%3A%2F%2Fwww.google.com%2F; __dtsu=4C301774685394D291D3AB624E4AA57E; _pubcid=8a5abbf9-164b-422f-b349-0e1ba702ea69; _cc_id=a4a99f9a552125d19ea447bfafb9c63b; global_ui_lang=id; HstCmu5004644=1779384259258; vidrama_chat_anon=45cc06417e3a261dc8f368a8; HstCnv5004644=48; cf_clearance=N5A.kyHMnJ7RBK3hOyqybB6KddOTpRsZyEiE.fgp5kM-1779713242-1.2.1.1-9YHMfsNOniF6J54T1_JEaJY6mYbVJWOz8Kkm0raJacrpotGOYzyN_gG.Kxb7kfPxOO1wYdSenqFW0HIUwqQ57F5gqyjRbwvS8_r8rLFxIbYHNWMAahrr.iKy0dsa1krg8mVhzXDilHK71X.Iszvd8uo_CwVzbHiVUurJ8eF1DyguF2fK1vFa68H3Z5HFzZhBvVaIle1tEW3443.tH9TYjQX.7HKB9SBI2ZHkNto2vDQ2F77XP3cLmCp7GPXINCG8mrZf6l5xsxuh_xyqNp1bIRyxkUhz9IooxQKp3yV9Crri9TFW9II5q0M50yOlhCROGsKwa0AkIkKtWi.pNc5ATg; HstCla5004644=1779713242621; HstPn5004644=2; HstPt5004644=93; HstCns5004644=54; panoramaId_expiry=1779799644224'

WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
    'Cookie': COOKIE
}

ns_id = '2056946805631225858'
ep_no = 10
url = f'https://vidrama.asia/api/netshortv2/episode/{ns_id}/{ep_no}?lang=id_ID'

# Try POST method
try:
    r_post = requests.post(url, headers=WEB_HDRS, verify=False, timeout=10)
    print("POST Status:", r_post.status_code)
except Exception as e:
    print("POST Error:", e)

# Try Cache-Control headers
hdrs = WEB_HDRS.copy()
hdrs['Cache-Control'] = 'no-cache'
hdrs['Pragma'] = 'no-cache'
r_hdr = requests.get(url, headers=hdrs, verify=False, timeout=10)
sub_url_hdr = r_hdr.json().get('data', {}).get('subtitles', [])[0].get('url')
print("Sub URL with Cache-Control headers:", sub_url_hdr[:150] + "...")

# Check if it has a fresh timestamp (unexpired)
# Expires parameter
import re
match = re.search(r'Expires=(\d+)', sub_url_hdr)
if match:
    exp = int(match.group(1))
    import datetime
    dt = datetime.datetime.fromtimestamp(exp)
    print(f"Expires timestamp: {exp} -> Date: {dt}")
    import time
    print("Is expired now:", exp < time.time())
