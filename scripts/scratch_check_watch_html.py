import re

with open('watch_865915.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Check title in html
title = re.findall(r'<title>(.*?)</title>', html)
print("Title in HTML:", title)

# Check self.__next_f blobs in watch_865915.html
blobs = re.findall(r'self\.__next_f\.push\(\[(.*?)\]\)', html, re.DOTALL)
print(f"Total blobs: {len(blobs)}")
for i, b in enumerate(blobs):
    if '865915' in b or 'pahlawan' in b.lower():
        print(f"Blob {i} mentions 865915/pahlawan:")
        print(b[:300])
    if 'notfound' in b.lower() or '404' in b:
        print(f"Blob {i} mentions 404/notfound:")
        print(b[:200])
