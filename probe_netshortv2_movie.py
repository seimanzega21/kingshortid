import requests
import re
import urllib3
urllib3.disable_warnings()

url = "https://vidrama.asia/movie/dewa-petir-sss-tersembunyi--2089169768653586433?provider=netshortv2&lang=id_ID"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}
r = requests.get(url, headers=headers, verify=False)
html = r.text

print(f"Status: {r.status_code}")

# Find any API URLs that contain 'netshort'
apis = re.findall(r'https?://[^\s\"\'\\]*netshort[^\s\"\'\\]*', html)
print("Found netshort URLs:")
for m in set(apis):
    print(m)

# Dump server components json
with open('movie.html', 'w', encoding='utf-8') as f:
    f.write(html)
