import requests
import re
import urllib3
urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0'}
r = requests.get('https://vidrama.asia/_next/static/chunks/ee836e364b166223.js', headers=headers, timeout=15, verify=False)
text = r.text

print(f"Length of ee836e364b166223.js: {len(text)}")
for m in re.finditer(r'createServerReference\("([a-f0-9]+)"[^)]*getEpisodeUrl', text):
    print("Action ID:", m.group(1), m.group(0))

# Search for getEpisodeUrl anywhere in text
for m in re.finditer(r'getEpisodeUrl', text):
    snippet = text[max(0, m.start()-100):min(len(text), m.end()+150)]
    print("--- getEpisodeUrl snippet ---")
    print(snippet)
