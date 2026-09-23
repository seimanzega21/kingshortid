import requests
import re
import urllib3
urllib3.disable_warnings()

# Let's inspect the chunks listed in watch_865915.html:
# /_next/static/chunks/b1801931ee7f37d7.js
# /_next/static/chunks/5a174e743556891f.js
# /_next/static/chunks/843978a330dc1c19.js
# /_next/static/chunks/a6dad97d9634a72d.js
# /_next/static/chunks/172579539fa70c75.js

# Let's download them with a larger timeout or retry
headers = {'User-Agent': 'Mozilla/5.0'}

chunks = [
    '/_next/static/chunks/b1801931ee7f37d7.js',
    '/_next/static/chunks/5a174e743556891f.js',
    '/_next/static/chunks/843978a330dc1c19.js',
    '/_next/static/chunks/a6dad97d9634a72d.js',
    '/_next/static/chunks/172579539fa70c75.js',
    '/_next/static/chunks/7c862900ddac2100.js',
]

for c in chunks:
    print(f"Fetching {c}...")
    for attempt in range(3):
        try:
            r = requests.get(f"https://vidrama.asia{c}", headers=headers, timeout=20, verify=False)
            if r.status_code == 200:
                print(f"  Success {c}, len={len(r.text)}")
                # Search for createServerReference
                refs = re.findall(r'createServerReference\("([a-f0-9]+)"[^"]*"([^"]+)"\)', r.text)
                for aid, name in refs:
                    if 'episode' in name.lower() or 'drama' in name.lower():
                        print(f"    ACTION: {name} -> {aid}")
                # Search for getEpisodeUrl in text
                if 'shortmax' in r.text.lower():
                    print("    Contains 'shortmax'!")
                break
        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {e}")
