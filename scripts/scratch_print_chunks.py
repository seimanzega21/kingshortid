import re

with open('watch_865915.html', 'r', encoding='utf-8') as f:
    html = f.read()

chunks = re.findall(r'src="(/_next/static/chunks/[^"]+)"', html)
for c in chunks:
    print(c)
