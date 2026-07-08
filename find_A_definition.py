# -*- coding: utf-8 -*-
import requests, re, urllib3, sys
urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

url = 'https://vidrama.asia/_next/static/chunks/123c8307fc6c5765.js'
r = requests.get(url, verify=False)
if r.ok:
    # Let's search for how variables 'A' and 'T' are initialized in the file.
    # Since they are in the module scope, let's search for:
    # `,A=` or `const A=` or `let A=` or `var A=`
    patterns = [
        r'\bA\s*=\s*[^,;]+',
        r'const\s+A\s*=\s*[^,;]+',
        r'let\s+A\s*=\s*[^,;]+',
        r'var\s+A\s*=\s*[^,;]+',
        r',\s*A\s*=\s*[^,;]+'
    ]
    for p in patterns:
        for m in re.finditer(p, r.text):
            # Print if it looks like an import or module reference
            text_match = m.group(0)
            if 'r(' in text_match or 'n(' in text_match or 'a(' in text_match or 'u(' in text_match or 'e(' in text_match or 's(' in text_match:
                print(f"Match: {text_match} at {m.start()}")
