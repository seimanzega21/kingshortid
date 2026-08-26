import requests
import re
import urllib3
urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0'}

with open('extract_js.py', 'r') as f:
    pass

import subprocess
out = subprocess.check_output(['python', 'extract_js.py'], text=True)
js_files = [x.strip() for x in out.split('\n') if x.strip()]

print(f"Scanning {len(js_files)} JS files...")

for j in js_files:
    url = f"https://vidrama.asia{j}"
    try:
        r = requests.get(url, headers=headers, verify=False, timeout=10)
        if r.ok:
            text = r.text
            # search for netshortv2 or provider logic
            if 'netshortv2' in text or 'proxy-' in text or 'api/' in text or 'm3u8' in text:
                matches = re.findall(r'[\"\']/(api/[a-zA-Z0-9_\-\/\.\?=\&]+)[\"\']', text)
                matches += re.findall(r'[\"\'](https?://[^\s\"\'\\]*api[^\s\"\'\\]*)[\"\']', text)
                if matches:
                    print(f"--- {j} ---")
                    for m in set(matches):
                        print("  ", m)
    except Exception as e:
        print(f"Error on {j}: {e}")

