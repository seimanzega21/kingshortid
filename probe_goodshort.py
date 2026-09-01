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
        matches = re.findall(r'[\'"`]/api/[^\'"`]+', c)
        print(f"Matches in {chunk_url}:", set(matches))
