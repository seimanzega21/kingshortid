import requests
import re
import urllib3
urllib3.disable_warnings()

url = "https://vidrama.asia/movie/dewa-petir-sss-tersembunyi--2089169768653586433?provider=netshortv2&lang=id_ID"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

r = requests.get(url, headers=headers, timeout=15, verify=False)
html = r.text

print(f"Status: {r.status_code}")
print(f"HTML size: {len(html)}")

# Find any JSON-like data or API calls
patterns = [
    r'https?://[^\s\"\'\\]+api[^\s\"\'\\]+',
    r'\"api[^\"]+\"',
    r'/api/[^\"]+'
]

print("Matches:")
for p in patterns:
    matches = set(re.findall(p, html))
    for m in list(matches)[:10]:
        print(m)
        
print("Let's look for netshortv2 specific:")
matches = re.findall(r'.{0,50}netshortv2.{0,50}', html)
for m in set(matches):
    print(m.strip())
