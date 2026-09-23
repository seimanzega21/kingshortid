import re

with open('movie_865915.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Look for watch URL
watch = re.findall(r'(/watch/[^"\'\s<>]+)', html)
print("Watch URLs found:")
for w in set(watch):
    print(" ", w)
