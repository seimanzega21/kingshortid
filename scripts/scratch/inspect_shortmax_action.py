import requests
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/'
}

r = requests.get('https://vidrama.asia/_next/static/chunks/43f5bb3acc7e88b0.js', headers=headers, verify=False)
js = r.text

# Let's inspect where shortmax calls q.getEpisodeUrl or similar
for m in re.finditer(r'"shortmax"===([a-zA-Z0-9_]+)', js):
    start = max(0, m.start() - 100)
    end = min(len(js), m.end() + 500)
    print("=== SHORTMAX MATCH ===")
    print(js[start:end])
    print()
