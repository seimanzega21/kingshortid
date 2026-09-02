import requests
import re
import json
WEB_HDRS = {'User-Agent': 'Mozilla/5.0'}
r = requests.get('https://vidrama.asia/provider/reelshort', headers=WEB_HDRS, verify=False)
matches = re.findall(r'href="/movie/([^"]+)', r.text)
print('Total /movie/ links:', len(matches))
print('Sample:', matches[:5])

# Also check for JSON data embedded in Next.js props
next_data = re.search(r'<script id="__NEXT_DATA__" type="application/json">([^<]+)</script>', r.text)
if next_data:
    try:
        data = json.loads(next_data.group(1))
        # drill down to get movies if possible
        print("Found __NEXT_DATA__")
    except:
        pass
