import requests
import re
import urllib3
urllib3.disable_warnings()

with open('watch_865915.html', 'r', encoding='utf-8') as f:
    html = f.read()

chunks = re.findall(r'src="(/_next/static/chunks/[^"]+)"', html)
headers = {'User-Agent': 'Mozilla/5.0'}

print(f"Total chunks: {len(chunks)}")
for c in set(chunks):
    try:
        r = requests.get(f'https://vidrama.asia{c}', headers=headers, timeout=10, verify=False)
        if 'createServerReference' in r.text:
            print(f"createServerReference in {c} (len={len(r.text)})")
            # find all refs with their exported name
            refs = re.findall(r'createServerReference\("([a-f0-9]+)"[^"]*"([^"]+)"\)', r.text)
            for action_id, name in refs:
                print(f"  {name} -> {action_id}")
            if not refs:
                # alternative pattern
                refs2 = re.findall(r'createServerReference\("([a-f0-9]+)"', r.text)
                print(f"  Found {len(refs2)} raw action IDs")
    except Exception as e:
        print(f"Error {c}: {e}")
