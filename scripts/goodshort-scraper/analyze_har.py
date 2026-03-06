import json
from collections import Counter
from urllib.parse import urlparse

# Load HAR file
with open('fresh_capture.har', 'r', encoding='utf-8') as f:
    har = json.load(f)

entries = har['log']['entries']

# Filter GoodShort API calls
goodshort_apis = [e for e in entries if 'goodreels' in e['request']['url'] or 'xintaicz' in e['request']['url']]

print(f'Total GoodShort API calls: {len(goodshort_apis)}')
print(f'Total all entries: {len(entries)}')

# Group by endpoint
urls = Counter([e['request']['url'].split('?')[0] for e in goodshort_apis])

print('\n=== TOP API ENDPOINTS ===')
for url, count in urls.most_common(15):
    print(f'{count:4d}x  {url}')

# Analyze request structure
print('\n=== SAMPLE REQUEST ANALYSIS ===')
for entry in goodshort_apis[:3]:
    req = entry['request']
    print(f'\nURL: {req["url"]}')
    print(f'Method: {req["method"]}')
    print('Headers:')
    for h in req['headers']:
        if h['name'].lower() in ['authorization', 'sign', 'token', 'x-', 'user-agent']:
            print(f'  {h["name"]}: {h["value"][:80]}...' if len(h["value"]) > 80 else f'  {h["name"]}: {h["value"]}')
