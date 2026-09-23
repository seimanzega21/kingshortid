import re

with open('movie_865915.html', 'r', encoding='utf-8') as f:
    text = f.read()

# search for episode-1-
pos = text.find('episode-1-')
if pos != -1:
    print(text[pos-100:pos+300])
else:
    print("episode-1- not found")

# search for episodeNum\":1\b or episodeNum\":1,
m = re.findall(r'\{[^{}]*episodeNum[^{}]*\}', text)
print(f"Total episode elements: {len(m)}")
for ep in m[:5]:
    print(ep)
