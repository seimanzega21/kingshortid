import re

with open('movie_865915.html', 'r', encoding='utf-8') as f:
    text = f.read()

defs = re.findall(r'(\w+):I\[(\d+),(\[[^\]]+\]),"([^"]+)"\]', text)
for d in defs:
    print(d)
