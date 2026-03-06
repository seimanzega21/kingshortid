#!/usr/bin/env python3
"""Find discovery/listing endpoints in HAR files"""
import json, sys, io
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Check all HARs for listing/discovery endpoints
for har_name in ['melolo4.har']:
    print(f"\n{'='*60}")
    print(f"  {har_name} — Discovery Endpoints")
    print(f"{'='*60}")
    
    with open(har_name, 'r', encoding='utf-8') as f:
        har = json.load(f)
    
    for entry in har['log']['entries']:
        url = entry['request']['url']
        # Only API domains
        if 'tmtreader.com' not in url and 'novelseradata' not in url:
            continue
        
        path = url.split('?')[0]
        resp_text = entry['response']['content'].get('text', '')
        resp_size = len(resp_text) if resp_text else 0
        
        # Skip tiny responses (logs, tracking)
        if resp_size < 500:
            continue
        
        # Print interesting endpoints
        short_path = path.replace('https://api.tmtreader.com/', '')
        print(f"\n  {short_path}")
        print(f"    Response: {resp_size} bytes")
        
        # Check if it contains book listings
        if resp_text:
            try:
                data = json.loads(resp_text)
                # Look for arrays of books
                def find_book_lists(obj, path="root", depth=0):
                    if depth > 4:
                        return
                    if isinstance(obj, dict):
                        for k, v in obj.items():
                            if isinstance(v, list) and len(v) > 3:
                                # Check if items have book_id or series_id
                                if v and isinstance(v[0], dict):
                                    keys = set(v[0].keys())
                                    if keys & {'book_id', 'series_id', 'book_name', 'series_title'}:
                                        names = [str(item.get('book_name','') or item.get('series_title',''))[:30] for item in v[:5]]
                                        print(f"    📚 {path}.{k}: list[{len(v)}] items")
                                        print(f"       Keys: {list(v[0].keys())[:10]}")
                                        print(f"       Names: {names}")
                            find_book_lists(v, f"{path}.{k}", depth+1)
                    elif isinstance(obj, list):
                        for i, item in enumerate(obj[:3]):
                            find_book_lists(item, f"{path}[{i}]", depth+1)
                
                find_book_lists(data)
            except:
                pass

# Also check what auth params are in the API URLs
print(f"\n{'='*60}")
print(f"  AUTH PARAMS ANALYSIS")
print(f"{'='*60}")

with open('melolo4.har', 'r', encoding='utf-8') as f:
    har = json.load(f)

for entry in har['log']['entries']:
    url = entry['request']['url']
    if 'multi_video_model' in url or 'bookmall' in url or 'video_detail' in url:
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        print(f"\n  Endpoint: {parsed.path}")
        for k in sorted(params.keys()):
            v = params[k][0]
            if len(v) > 60:
                v = v[:60] + '...'
            print(f"    {k}: {v}")
        break
