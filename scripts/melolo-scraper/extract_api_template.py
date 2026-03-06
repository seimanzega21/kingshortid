#!/usr/bin/env python3
"""Extract full API request templates from melolo4.har for auto-discovery"""
import json, sys, io
from urllib.parse import urlparse, parse_qs, urlencode
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open('melolo4.har', 'r', encoding='utf-8') as f:
    har = json.load(f)

# 1. Extract bookmall/cell/change request template
print("=" * 70)
print("  bookmall/cell/change/v1/ — FULL REQUEST")
print("=" * 70)

for entry in har['log']['entries']:
    url = entry['request']['url']
    if 'bookmall/cell/change/v1/' not in url:
        continue
    
    parsed = urlparse(url)
    print(f"\n  Base URL: {parsed.scheme}://{parsed.netloc}{parsed.path}")
    
    # Headers
    headers = {h['name']: h['value'] for h in entry['request']['headers']}
    print(f"\n  Key headers:")
    for k in sorted(headers.keys()):
        if k.lower() in ['cookie', 'x-tt-token', 'authorization', 'x-argus', 'x-gorgon', 'x-khronos', 'x-ladon', 'x-ss-req-ticket']:
            print(f"    {k}: {headers[k][:80]}...")
        elif k.lower() in ['host', 'user-agent', 'content-type', 'accept', 'x-helios', 'passport-sdk-version']:
            print(f"    {k}: {headers[k]}")
    
    # Full query params
    params = parse_qs(parsed.query)
    print(f"\n  Query params ({len(params)} total):")
    for k in sorted(params.keys()):
        v = params[k][0]
        if len(v) > 100:
            print(f"    {k}: {v[:80]}...")
        else:
            print(f"    {k}: {v}")
    
    # POST body?
    method = entry['request']['method']
    print(f"\n  Method: {method}")
    if method == 'POST' and 'postData' in entry['request']:
        print(f"  PostData: {entry['request']['postData'].get('text', '')[:200]}")
    
    break

# 2. Extract video_detail request template  
print(f"\n\n{'=' * 70}")
print("  video_detail/v1/ — FULL REQUEST")
print("=" * 70)

for entry in har['log']['entries']:
    url = entry['request']['url']
    if 'video_detail/v1/' not in url or 'multi' in url:
        continue
    
    parsed = urlparse(url)
    print(f"\n  Base URL: {parsed.scheme}://{parsed.netloc}{parsed.path}")
    
    headers = {h['name']: h['value'] for h in entry['request']['headers']}
    print(f"\n  Key headers:")
    for k in sorted(headers.keys()):
        if k.lower() in ['cookie', 'x-tt-token', 'x-argus', 'x-gorgon', 'x-khronos', 'x-ladon', 'x-ss-req-ticket', 'host', 'user-agent', 'content-type']:
            val = headers[k]
            if len(val) > 100:
                print(f"    {k}: {val[:80]}...")
            else:
                print(f"    {k}: {val}")
    
    params = parse_qs(parsed.query)
    print(f"\n  Query params ({len(params)} total):")
    for k in sorted(params.keys()):
        v = params[k][0]
        if len(v) > 100:
            print(f"    {k}: {v[:80]}...")
        else:
            print(f"    {k}: {v}")
    
    method = entry['request']['method']
    print(f"\n  Method: {method}")
    if method == 'POST' and 'postData' in entry['request']:
        print(f"  PostData: {entry['request']['postData'].get('text', '')[:500]}")
    
    break

# 3. Extract bookmall/tab request template (cell_id is needed for cell/change)
print(f"\n\n{'=' * 70}")  
print("  bookmall/tab/v1/ — CELL_IDs")
print("=" * 70)

for entry in har['log']['entries']:
    url = entry['request']['url']
    if 'bookmall/tab/v1/' not in url:
        continue
    text = entry['response']['content'].get('text', '')
    if not text: continue
    try: data = json.loads(text)
    except: continue
    
    tabs = data.get('data', {}).get('book_tab_infos', [])
    for tab in tabs:
        cells = tab.get('cells', [])
        for cell in cells:
            cell_id = cell.get('id', cell.get('cell_id', cell.get('cid', '')))
            print(f"  cell id={cell_id}, cid={cell.get('cid','')}, type={cell.get('cell_type','')}")
            print(f"  has_more={cell.get('has_more')}, next_offset={cell.get('next_offset')}")
            
            # Check cell_data
            cd = cell.get('cell_data', [])
            if isinstance(cd, list) and cd:
                print(f"  cell_data: list[{len(cd)}]")
                if isinstance(cd[0], dict):
                    print(f"  cell_data[0] keys: {list(cd[0].keys())[:10]}")
    break
