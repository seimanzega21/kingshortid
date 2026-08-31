import requests
import re
url = 'https://vidrama.asia/watch/rahasia-penjual-terbaik--2039988866577907712/1?provider=dramanova2&lang=in'
hdrs = {'User-Agent': 'Mozilla/5.0'}
r = requests.get(url, headers=hdrs)
chunks = re.findall(r'src="(/_next/static/chunks/[^"]+)"', r.text)
for chunk in chunks:
    chunk_url = "https://vidrama.asia" + chunk
    c = requests.get(chunk_url, headers=hdrs).text
    if 'dramanova2' in c or '/api/' in c:
        print(f"Found in {chunk_url}")
        matches = re.findall(r'[\'"`]/api/[^\'"`]+', c)
        print(set(matches))
