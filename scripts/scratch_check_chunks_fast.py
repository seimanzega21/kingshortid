import requests
import re
import urllib3
urllib3.disable_warnings()

headers = {'User-Agent': 'Mozilla/5.0'}
chunks = [
    '/_next/static/chunks/8a450f23ac1062d3.js',
    '/_next/static/chunks/4ba947795445f824.js',
    '/_next/static/chunks/111e904f7cf906e0.js',
    '/_next/static/chunks/c13d18b2b15b9a28.js',
    '/_next/static/chunks/turbopack-6151e19be1db73ec.js',
    '/_next/static/chunks/a44235986dc198f3.js',
    '/_next/static/chunks/75b5c11343842a8d.js',
    '/_next/static/chunks/af310da47ea4a263.js',
    '/_next/static/chunks/97f34b24eaad82e9.js',
    '/_next/static/chunks/9b9ab7ac65fbb304.js',
    '/_next/static/chunks/e6c9da931421259f.js',
    '/_next/static/chunks/ee836e364b166223.js',
    '/_next/static/chunks/fa58348e1cfbeff8.js',
    '/_next/static/chunks/5a174e743556891f.js',
    '/_next/static/chunks/b1801931ee7f37d7.js',
    '/_next/static/chunks/172579539fa70c75.js',
    '/_next/static/chunks/843978a330dc1c19.js',
    '/_next/static/chunks/a6dad97d9634a72d.js',
    '/_next/static/chunks/7c862900ddac2100.js'
]

for c in chunks:
    try:
        r = requests.get(f'https://vidrama.asia{c}', headers=headers, timeout=5, verify=False)
        text = r.text
        if 'shortmax' in text.lower():
            print(f"Found 'shortmax' in {c}")
        if 'getEpisodeUrl' in text:
            print(f"Found 'getEpisodeUrl' in {c}")
            for m in re.finditer(r'createServerReference\("([a-f0-9]+)"[^)]*getEpisodeUrl', text):
                print("  Action ID:", m.group(1))
    except Exception as e:
        print(f"Error {c}: {e}")
