import json
from urllib.parse import urlparse, parse_qs

# Load HAR
with open('fresh_capture.har', 'r', encoding='utf-8') as f:
    har = json.load(f)

entries = har['log']['entries']
goodshort_apis = [e for e in entries if 'api-akm.goodreels' in e['request']['url']]

print(f'=== GoodShort API Calls: {len(goodshort_apis)} ===\n')

# Group by path
from collections import defaultdict
by_path = defaultdict(list)
for e in goodshort_apis:
    path = urlparse(e['request']['url']).path
    by_path[path].append(e)

print('API Endpoints:')
for path, reqs in sorted(by_path.items(), key=lambda x: len(x[1]), reverse=True):
    print(f'  {len(reqs):3d}x  {path}')

print('\n=== DETAILED REQUEST ANALYSIS ===\n')

# Analyze a few key endpoints
key_endpoints = [
    '/hwycclientreels/book/list',
    '/hwycclientreels/chapter/list', 
    '/hwycclientreels/chapter/video',
    '/hwycclientreels/book/detail'
]

for endpoint in key_endpoints:
    matching = [e for e in goodshort_apis if endpoint in e['request']['url']]
    if matching:
        e = matching[0]
        req = e['request']
        
        print(f'\n{"="*70}')
        print(f'ENDPOINT: {endpoint}')
        print(f'{"="*70}')
        print(f'Full URL: {req["url"]}')
        print(f'Method: {req["method"]}')
        
        # Headers
        print('\nKey Headers:')
        for h in req['headers']:
            name = h['name'].lower()
            if name in ['authorization', 'sign', 'token', 'x-timestamp', 'x-device', 'user-agent', 'content-type']:
                value = h['value']
                if len(value) > 100:
                    value = value[:100] + '...'
                print(f'  {h["name"]}: {value}')
        
        # POST data
        if req['method'] == 'POST' and 'postData' in req:
            print('\nPOST Data:')
            if 'text' in req['postData']:
                data = req['postData']['text']
                if len(data) > 500:
                    data = data[:500] + '...'
                print(f'  {data}')
        
        # Query params
        parsed = urlparse(req['url'])
        if parsed.query:
            print('\nQuery Parameters:')
            params = parse_qs(parsed.query)
            for k, v in params.items():
                print(f'  {k}: {v[0]}')
        
        # Response
        print(f'\nResponse Status: {e["response"]["status"]}')
        if 'content' in e['response'] and 'text' in e['response']['content']:
            resp_text = e['response']['content']['text']
            if resp_text:
                try:
                    resp_json = json.loads(resp_text)
                    print(f'Response Sample:')
                    print(f'  {json.dumps(resp_json, ensure_ascii=False, indent=2)[:500]}...')
                except:
                    print(f'  {resp_text[:300]}...')
