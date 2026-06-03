import requests
import time
import urllib3

urllib3.disable_warnings()

BOOK_ID = '42000007062'
COOKIE = '_fbp=fb.1.1770653154777.876935444165455244; _tt_enable_cookie=1; _ttp=01KH1JE0K4H648BY6E3FQ6EXRZ_.tt.1; _ga=GA1.1.1826262121.1771037718; HstCfa5004644=1772873251576; c_ref_5004644=https%3A%2F%2Fwww.google.com%2F; __dtsu=4C301774685394D291D3AB624E4AA57E; _pubcid=8a5abbf9-164b-422f-b349-0e1ba702ea69; _cc_id=a4a99f9a552125d19ea447bfafb9c63b; global_ui_lang=id; HstCmu5004644=1779384259258; vidrama_chat_anon=45cc06417e3a261dc8f368a8; HstCnv5004644=48; cf_clearance=N5A.kyHMnJ7RBK3hOyqybB6KddOTpRsZyEiE.fgp5kM-1779713242-1.2.1.1-9YHMfsNOniF6J54T1_JEaJY6mYbVJWOz8Kkm0raJacrpotGOYzyN_gG.Kxb7kfPxOO1wYdSenqFW0HIUwqQ57F5gqyjRbwvS8_r8rLFxIbYHNWMAahrr.iKy0dsa1krg8mVhzXDilHK71X.Iszvd8uo_CwVzbHiVUurJ8eF1DyguF2fK1vFa68H3Z5HFzZhBvVaIle1tEW3443.tH9TYjQX.7HKB9SBI2ZHkNto2vDQ2F77XP3cLmCp7GPXINCG8mrZf6l5xsxuh_xyqNp1bIRyxkUhz9IooxQKp3yV9Crri9TFW9II5q0M50yOlhCROGsKwa0AkIkKtWi.pNc5ATg; HstCla5004644=1779713242621; HstPn5004644=2; HstPt5004644=93; HstCns5004644=54; panoramaId_expiry=1779799644224'

VIDRAMA_HDR = {
    'accept': '*/*',
    'accept-language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
    'cookie': COOKIE,
    'priority': 'u=1, i',
    'referer': f'https://vidrama.asia/watch/janji-kuno--{BOOK_ID}/28?provider=dramabox3&lang=in',
    'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Mobile Safari/537.36'
}

# Get watch page API response for ep 28
print("Fetching Watch API response for ep 28...")
url = f'https://vidrama.asia/api/dramabox3/watch?bookId={BOOK_ID}&episode=28&lang=in'
r = requests.get(url, headers=VIDRAMA_HDR, verify=False)
if r.ok:
    data = r.json()
    print("Success:", data.get('success'))
    qualities = data.get('availableQualities', [])
    for q in qualities:
        print(f"Quality: {q['label']} -> {q['url']}")
        
        # Test downloading first 100KB of the stream
        t0 = time.time()
        try:
            stream_r = requests.get(q['url'], headers=VIDRAMA_HDR, stream=True, timeout=10, verify=False)
            print(f"  Stream status code: {stream_r.status_code}")
            print(f"  Stream headers: {dict(stream_r.headers)}")
            size = 0
            for chunk in stream_r.iter_content(chunk_size=1024):
                size += len(chunk)
                if size >= 100 * 1024:
                    break
            print(f"  Downloaded 100KB successfully in {time.time() - t0:.2f}s")
        except Exception as e:
            print(f"  Failed: {e}")
else:
    print(f"Failed: {r.status_code}")
