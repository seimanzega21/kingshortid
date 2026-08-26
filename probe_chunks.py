import requests
import re
import urllib3
urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0'}
chunks = [
    '9717f0bc7dd570c2.js',
    '5bc638f308e652a6.js',
    'afed3840064a6330.js',
    'fa58348e1cfbeff8.js',
    '85645474589c9371.js',
    'c604b5746f913661.js',
    '75b5c11343842a8d.js'
]

for chunk in chunks:
    url = f"https://vidrama.asia/_next/static/chunks/{chunk}"
    r = requests.get(url, headers=headers, verify=False)
    if r.ok:
        text = r.text
        if 'netshortv2' in text or 'api/' in text:
            print(f"Found in {chunk}:")
            # Find /api/ URLs
            apis = set(re.findall(r'[\"\']/api/[^\/\s\"\']+[\"\']', text))
            for a in apis:
                print("  API:", a)
