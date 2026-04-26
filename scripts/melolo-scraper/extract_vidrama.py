import requests
import re

print("Fetching vidrama.asia...")
html = requests.get('https://vidrama.asia', headers={'User-Agent': 'Mozilla/5.0'}).text

print("Looking for JS chunks...")
js_urls = re.findall(r'src=\"(/_next/static/chunks/[^\"]+\.js)\"', html)

for js in js_urls:
    print(f"Checking {js}...")
    js_text = requests.get('https://vidrama.asia' + js, headers={'User-Agent': 'Mozilla/5.0'}).text
    keys = re.findall(r'eyJh[\w\.\-]+', js_text)
    if keys:
        print(f'Found token in {js}: {keys[0]}')
        break
