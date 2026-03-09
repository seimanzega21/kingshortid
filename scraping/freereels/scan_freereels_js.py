"""
Scan FreeReels main JS bundle for:
1. Tab feed API endpoint + correct params
2. Drama info/list endpoints
3. Series ID format
"""
import requests, re, sys, json

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_URL = 'https://free-reels.com'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Linux; Android 12)'}

# Get main page to find JS bundles
print('Fetching FreeReels homepage...')
r = requests.get(f'{BASE_URL}/', headers=HEADERS, timeout=20)
html = r.text

# Extract JS bundle URLs
js_urls = re.findall(r'/assets/([^"\'<>\s]+\.js)', html)
js_urls = list(set(js_urls))
print(f'JS bundles: {js_urls[:10]}')

# Scan ALL JS chunks for API patterns
all_found = {}
AUDIO_PATTERNS = [
    'tab.feed', 'tab/feed', 'tabFeed',
    'tab.content', 'tab/content',
    'drama.list', 'drama/list', 'dramaList',
    'drama.info', 'drama/info',
    'series_id', 'seriesId',
    'external_audio', 'dubbed',
    'frv2-api',
    '/homepage/v2/',
    'tab_key', 'tabKey',
    'page_size', 'pageSize',
]

for js_file in js_urls:
    url = f'{BASE_URL}/assets/{js_file}'
    try:
        r2 = requests.get(url, headers=HEADERS, timeout=15)
        js = r2.text
        
        hits = {}
        for pat in AUDIO_PATTERNS:
            if pat in js:
                # Get context around pattern
                idx = js.index(pat)
                ctx = js[max(0, idx-100):idx+200]
                hits[pat] = ctx[:250]
        
        if hits:
            print(f'\n=== {js_file} ({len(js):,} chars) ===')
            all_found[js_file] = hits
            for pat, ctx in hits.items():
                print(f'  [{pat}]:')
                print(f'  {ctx[:200]}')
            
            # Save this chunk
            with open(f'fr_chunk_{js_file[:30]}.txt', 'w', encoding='utf-8', errors='replace') as f:
                f.write(js[:50000])
    except Exception as e:
        pass

# Find the main API chunk
print('\n\nLooking for frv2-api endpoint in JS...')
for js_file in js_urls:
    url = f'{BASE_URL}/assets/{js_file}'
    try:
        r2 = requests.get(url, headers=HEADERS, timeout=15)
        js = r2.text
        
        # Look for all API paths
        paths = re.findall(r'["\']/(frv2-api/[^"\']{3,60})["\']', js)
        if paths:
            print(f'\n{js_file}: frv2-api paths found:')
            for p in sorted(set(paths)):
                print(f'  /{p}')
            
            # Also look for tab feed body structure
            for m in re.finditer(r'tab.feed|tab_feed|tabFeed', js, re.IGNORECASE):
                ctx = js[max(0, m.start()-50):m.end()+300]
                print(f'\n  tab feed context: {ctx[:300]}')
    except: pass
