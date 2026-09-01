import requests
import re
url = 'https://vidrama.asia/watch/kiamat-datang-aku-beli-istri--31001700648/1?provider=goodshortv2&lang=in'
hdrs = {'User-Agent': 'Mozilla/5.0'}
r = requests.get(url, headers=hdrs)
chunks = re.findall(r'src="(/_next/static/chunks/[^"]+)"', r.text)
for chunk in chunks:
    chunk_url = "https://vidrama.asia" + chunk
    c = requests.get(chunk_url, headers=hdrs).text
    if 'goodshortv2' in c:
        for match in re.finditer(r'goodshortv2', c):
            idx = match.start()
            print(f"[{chunk_url}]:", c[max(0, idx-80):idx+80])
