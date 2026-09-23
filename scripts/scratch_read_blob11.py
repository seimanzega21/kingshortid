import re

with open('movie_865915.html', 'r', encoding='utf-8') as f:
    text = f.read()

blobs = re.findall(r'self\.__next_f\.push\(\[(.*?)\]\)', text, re.DOTALL)
print("Blob 11:\n", blobs[11])
