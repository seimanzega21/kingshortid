import requests
import urllib3
import re
import os

urllib3.disable_warnings()

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

chunks = [
    "1dac845e742fab48.js",
    "b1801931ee7f37d7.js",
    "bd616997b156d120.js",
    "f45415b48f7fb920.js",
    "f543ba853a1e59a9.js",
]

os.makedirs('scratch/watch_js', exist_ok=True)

for c in chunks:
    url = f"https://vidrama.asia/_next/static/chunks/{c}"
    print(f"Downloading: {url}...")
    try:
        r = requests.get(url, headers=headers, verify=False, timeout=15)
        if r.ok:
            filepath = os.path.join('scratch/watch_js', c)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(r.text)
            print(f"  Saved {len(r.text)} chars.")
            
            # Simple keyword search
            for kw in ['idrama2', 'idrama', 'proxy', 'api/']:
                matches = list(re.finditer(kw, r.text, re.IGNORECASE))
                if matches:
                    print(f"    --> Found '{kw}' {len(matches)} times.")
                    for m in matches[:2]:
                        pos = m.start()
                        print(f"      Context: {r.text[max(0, pos-100):min(len(r.text), pos+150)]}")
        else:
            print(f"  Failed: HTTP {r.status_code}")
    except Exception as e:
        print("  Error:", e)
