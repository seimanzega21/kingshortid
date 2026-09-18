import requests
import urllib3
import re
import json

urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

urls = [
    'https://vidrama.asia/?lang=id',
    'https://vidrama.asia/movie?lang=id',
    'https://vidrama.asia/dramawave-v2?lang=id'
]

movie_links = set()
for u in urls:
    try:
        r = requests.get(u, headers=headers, verify=False, timeout=15)
        matches = re.findall(r'/movie/[a-zA-Z0-9_\-\?=&;]+', r.text)
        for m in matches:
            if 'provider=melolov3' in m:
                movie_links.add(m)
        print(f"Checked {u} -> found {len(matches)} movie links, {len(movie_links)} melolov3")
    except Exception as e:
        print(f"Error {u}: {e}")

print("Total unique melolov3 links found from pages:", len(movie_links))
for link in list(movie_links)[:10]:
    print("  ", link)
