"""
Find all Vite chunks from the index JS bundle by looking for 
the Vite chunk map structure: e={[id]:"hash",...}
"""
import requests, re, json, sys, time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

idx_url_r = requests.get('https://m.mydramawave.com/free-app/', timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
idx_url = re.search(r'(https://static-v1\.mydramawave\.com/[^\s"\']+index[^\s"\']+\.js)', idx_url_r.text).group(1)
jr = requests.get(idx_url, timeout=30)
idx_js = jr.text
base = 'https://static-v1.mydramawave.com/frontend_static/assets'

# Vite builds a map like: (e=>{e[0]="BjpPc9T6",e[1]="...",...})
# or: {"0":"hash1","1":"hash2",...}
# Look for 8-char hex codes which are chunk hashes
hex_hashes = set(re.findall(r'\b([A-Za-z0-9]{8})\b', idx_js))
print(f'Potential hashes: {len(hex_hashes)}')

# Filter: try to build URLs and see which ones exist
# Vite chunk names have format: [name]-[hash].js
# Let's find patterns like 'name-hash.js' embedded in the index
chunk_patterns = re.findall(r'[a-zA-Z][a-zA-Z0-9-]*-[A-Za-z0-9]{8}\.js', idx_js)
unique_chunks = list(set(chunk_patterns))
print(f'Chunk file patterns: {len(unique_chunks)}')
for c in sorted(unique_chunks)[:20]:
    print(f'  {c}')

# Scan these specific chunks for h5-api endpoints
all_endpoints = {}
scanned = 0
for chunk_file in unique_chunks:
    url = f'{base}/{chunk_file}'
    try:
        r2 = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        if r2.status_code != 200: continue
        js = r2.text
        scanned += 1
        eps = re.findall(r'["\']/(h5-api/[^"\']{3,80})["\']', js)
        for ep in set(eps):
            all_endpoints.setdefault(ep, []).append(chunk_file)
        # Also find dubbed-related
        if re.search(r'dubb|dubbed', js, re.IGNORECASE):
            dubbed = re.findall(r'.{0,50}dubb.{0,100}', js, re.IGNORECASE)[:3]
            print(f'  DUBBED in {chunk_file}: {dubbed}')
    except: pass

print(f'\nScanned {scanned}/{len(unique_chunks)} chunks')
print('All endpoints:')
for ep in sorted(all_endpoints.keys()):
    print(f'  /{ep}')

with open('all_endpoints.json', 'w', encoding='utf-8') as f:
    json.dump(all_endpoints, f, ensure_ascii=False, indent=2)
