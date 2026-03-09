"""
Deep read use-series-item-BjpPc9T6.js to find:
1. Exact API endpoint + body for fetching episodes with audio tracks
2. external_audio_h264_m3u8 field structure
3. How audiotrack_language param is used in the API call
"""
import requests, re, json, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

base = 'https://static-v1.mydramawave.com/frontend_static/assets'
r = requests.get(f'{base}/use-series-item-BjpPc9T6.js', timeout=20,
                 headers={'User-Agent': 'Mozilla/5.0'})
js = r.text
print(f'Chunk: {len(js):,} chars')

# Find ALL context around external_audio (this is the key)
print('\n=== ALL external_audio contexts ===')
seen = set()
for m in re.finditer(r'external_audio', js, re.IGNORECASE):
    ctx = js[max(0, m.start()-300):m.end()+400]
    if ctx[:40] not in seen:
        seen.add(ctx[:40])
        print(f'\n[@ {m.start()}]:')
        print(ctx[:600])

# Find ALL h5-api paths in this chunk
print('\n=== API paths in use-series-item ===')
eps = set(re.findall(r'["\']/(h5-api/[^"\']{3,80})["\']', js) +
          re.findall(r'["\']/(frv2-api/[^"\']{3,80})["\']', js))
for ep in sorted(eps): print(f'  /{ep}')

# Find audio_language param
print('\n=== audiotrack_language usage ===')
for m in re.finditer(r'audiotrack|audio_language|audio_lang', js, re.IGNORECASE):
    ctx = js[max(0, m.start()-100):m.end()+250]
    if ctx[:40] not in seen:
        seen.add(ctx[:40])
        print(f'\n[{m.group()} @ {m.start()}]: {ctx[:350]}')

# Find any function that makes API call with audio params
print('\n=== API calls with language/audio params ===')
for m in re.finditer(r'\.(post|get)\(', js, re.IGNORECASE):
    ctx_start = m.start()
    ctx = js[ctx_start:ctx_start+200]
    if any(k in ctx.lower() for k in ['audio', 'lang', 'episode', 'play', 'h264', 'm3u8']):
        print(f'\n[call @ {m.start()}]: {ctx[:200]}')
