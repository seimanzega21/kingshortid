import requests
import re
c = requests.get('https://vidrama.asia/_next/static/chunks/43f5bb3acc7e88b0.js', headers={'User-Agent': 'Mozilla/5.0'}).text

# Since javascript gets minified, it might be `async function $(...` or `const $ = async (...`
idx = c.find('goodshort/stream?bookId')
if idx != -1:
    print(c[max(0, idx-200):idx+200])

idx = c.find('goodshort/detail')
if idx != -1:
    print("Found detail:", c[max(0, idx-200):idx+200])
