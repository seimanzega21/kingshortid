import re
text = open('payload.txt', encoding='utf-8').read()
urls = set(re.findall(r'https?://[^\"]+\.(?:jpg|jpeg|png|webp)', text))
for u in urls:
    print(u)
