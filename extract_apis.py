import requests
import re
url = 'https://vidrama.asia/_next/static/chunks/43f5bb3acc7e88b0.js'
c = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}).text
matches = re.findall(r'[\'"`]/api/[^\'"`]+', c)
for m in set(matches):
    if 'good' in m.lower():
        print(m)
