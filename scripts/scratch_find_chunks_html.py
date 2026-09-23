import re

with open('watch_865915.html', 'r', encoding='utf-8') as f:
    html = f.read()

# In Next.js app router, chunks are referenced in script tags and in the push blobs
scripts = re.findall(r'<script[^>]*src="([^"]+)"', html)
print("Scripts in HTML:")
for s in scripts:
    print(" ", s)

# Also check inside self.__next_f.push
chunks_in_blobs = re.findall(r'/[_a-zA-Z0-9\-\.]+\.js', html)
print("\nUnique JS in blobs:")
for j in sorted(set(chunks_in_blobs)):
    if 'chunk' in j:
        print(" ", j)
