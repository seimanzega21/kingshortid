import requests
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/'
}

r = requests.get('https://vidrama.asia/_next/static/chunks/43f5bb3acc7e88b0.js', headers=headers, verify=False)
js = r.text

# Look around var q=e.i(...) or q.getEpisodeUrl
# In previous snippet:
# var q=e.i(4621427),W=e.i(2084030)
# Let's search for module 4621427 and 2084030
for m in re.finditer(r'4621427|2084030', js):
    start = max(0, m.start() - 100)
    end = min(len(js), m.end() + 200)
    print("Match module:")
    print(js[start:end])

# Also check other chunks that might define these modules
# Or let's search for createServerReference with getEpisodeUrl
for m in re.finditer(r'createServerReference\([^)]*getEpisodeUrl', js):
    start = max(0, m.start() - 50)
    end = min(len(js), m.end() + 50)
    print("Server reference:")
    print(js[start:end])
