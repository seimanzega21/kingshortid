import re

with open('movie_865915.html', 'r', encoding='utf-8') as f:
    text = f.read()

scripts = re.findall(r'<script[^>]*src="([^"]+)"', text)
print("Scripts in movie_865915.html:")
for s in scripts:
    print(" ", s)

# Let's inspect self.__next_f blobs in movie_865915.html
blobs = re.findall(r'self\.__next_f\.push\(\[(.*?)\]\)', text, re.DOTALL)
print(f"Total blobs: {len(blobs)}")
for i, b in enumerate(blobs):
    if '865915' in b or 'pahlawan' in b.lower():
        print(f"Blob {i} has 865915, len={len(b)}")
        # print snippet
        print(b[:300])
        print("...")
        print(b[-300:])
