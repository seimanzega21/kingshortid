import re
with open('stardust.html', 'r', encoding='utf-8') as f:
    text = f.read()

slugs = set(re.findall(r'href="/movie/([^"?]+)', text))
print("Found slugs:")
for s in slugs:
    if '--' in s:
        print(s)
