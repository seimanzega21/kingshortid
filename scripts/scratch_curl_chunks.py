import requests
import re
import urllib3
urllib3.disable_warnings()

# In Next.js, server actions manifest is generated at build time,
# or client components importing server actions contain createServerReference.
# Let's inspect the chunk files from watch_865915.html.
# But earlier, downloading some chunks timed out because requests without stream or bad connection.
# Let's write a python script that downloads the chunk with curl or requests with small chunk size and no keep-alive.

import subprocess

chunks = [
    '5a174e743556891f',
    'b1801931ee7f37d7',
    '172579539fa70c75',
    '843978a330dc1c19',
    'a6dad97d9634a72d',
    '7c862900ddac2100'
]

for c in chunks:
    url = f"https://vidrama.asia/_next/static/chunks/{c}.js"
    out_file = f"chunk_{c}.js"
    print(f"Downloading {c} via curl...")
    res = subprocess.run(['curl.exe', '-s', '-k', '-A', 'Mozilla/5.0', url, '-o', out_file], timeout=30)
    print(f"Curl return code: {res.returncode}")
    try:
        with open(out_file, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
        print(f"  Size of {c}: {len(text)}")
        if 'createServerReference' in text:
            print(f"  -> createServerReference found in {c}!")
            refs = re.findall(r'createServerReference\("([a-f0-9]+)"[^"]*"([^"]+)"\)', text)
            for aid, name in refs:
                print(f"     {name}: {aid}")
        if 'shortmax' in text.lower():
            print(f"  -> 'shortmax' found in {c}!")
    except Exception as e:
        print("  Read error:", e)
