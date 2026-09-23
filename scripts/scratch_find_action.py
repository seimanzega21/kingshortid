import requests
import re
import urllib3
urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0'}
with open('watch_865915.html', 'r', encoding='utf-8') as f:
    html = f.read()

chunks = re.findall(r'src="(/_next/static/chunks/[^"]+)"', html)
print(f"Chunks count: {len(chunks)}")

for c in set(chunks):
    res = requests.get(f'https://vidrama.asia{c}', headers=headers, verify=False)
    if 'getEpisodeUrl' in res.text:
        print(f"Found 'getEpisodeUrl' in {c}!")
        for m in re.finditer(r'createServerReference\("([a-f0-9]+)"[^)]*getEpisodeUrl', res.text):
            print("  Action ID:", m.group(1), m.group(0))
        # check around shortmax
        for m in re.finditer(r'shortmax', res.text, re.IGNORECASE):
            sub = res.text[max(0, m.start()-50):min(len(res.text), m.end()+100)]
            print("  Shortmax snippet:", sub)
