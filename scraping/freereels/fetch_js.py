"""Extract pe() function and check login headers from DramaWave JS bundle."""
import requests, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

r = requests.get('https://m.mydramawave.com/free-app/', timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
scripts = re.findall(r'https://static-v1\.mydramawave\.com/[^\s"\'<>]+\.js', r.text)

results = []
for js_url in scripts:
    if 'index' not in js_url:
        continue
    jr = requests.get(js_url, timeout=30)
    js = jr.text

    # Find pe() function definition
    for m in re.finditer(r'\bpe=\(\)', js):
        ctx = js[max(0, m.start()-20):m.end()+400]
        results.append(f'=== pe() def @ {m.start()} ===\n{ctx}')

    # Find Dn (axios instance) configuration - check if headers are set
    for m in re.finditer(r'new Cr\(', js):
        ctx = js[max(0, m.start()-20):m.end()+300]
        results.append(f'=== Cr (axios instance) @ {m.start()} ===\n{ctx}')

    # Look for the Cr class / axios config / interceptors
    for m in re.finditer(r'bp\s*=\s*\{', js):
        ctx = js[max(0, m.start()-10):m.end()+500]
        results.append(f'=== bp (config) @ {m.start()} ===\n{ctx}')

    # Find app-name header setup
    for m in re.finditer(r'app-name|app_name|appName', js, re.IGNORECASE):
        ctx = js[max(0, m.start()-80):m.end()+200]
        results.append(f'=== app-name header @ {m.start()} ===\n{ctx}')
    break

with open('js_pe.txt', 'w', encoding='utf-8', errors='replace') as f:
    for txt in results[:20]:
        f.write(txt + '\n\n')
print(f'Saved {len(results)} snippets to js_pe.txt')
