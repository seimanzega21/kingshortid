import requests
import re
import urllib3
urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0'}
r = requests.get('https://vidrama.asia/_next/static/chunks/turbopack-6151e19be1db73ec.js', headers=headers, verify=False)
print("turbopack chunk len:", len(r.text))
print("turbopack preview:\n", r.text[:500])

# Check for any action or reference patterns in turbopack chunk
for m in re.finditer(r'createServerReference|action|server', r.text, re.IGNORECASE):
    print("Match:", r.text[max(0, m.start()-50):min(len(r.text), m.end()+50)])
