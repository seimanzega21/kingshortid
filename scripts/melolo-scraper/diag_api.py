#!/usr/bin/env python3
"""Quick diagnostic: check what multi_video_model returns"""
import json, sys, io, time, requests
from pathlib import Path
from urllib.parse import urlparse, parse_qs

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

har_path = Path('melolo4.har')
with open(har_path, 'r', encoding='utf-8') as f:
    har = json.load(f)

# Find multi_video_model request
for entry in har['log']['entries']:
    url = entry['request']['url']
    if 'multi_video_model' not in url:
        continue
    
    req = entry['request']
    parsed = urlparse(url)
    headers = {h['name'].lower(): h['value'] for h in req['headers']}
    params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
    
    print(f"Original URL: {url[:120]}...")
    print(f"Method: {req['method']}")
    print(f"Original vids param: {params.get('vids', 'NOT FOUND')[:80]}...")
    
    # Try the original request as-is
    print(f"\n--- Test 1: Replay original request ---")
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        print(f"Status: {resp.status_code}")
        data = resp.json()
        print(f"Response keys: {list(data.keys())}")
        print(f"data.data keys: {list(data.get('data', {}).keys())[:10]}")
        
        # Check for video_urls
        vid_data = data.get('data', {})
        if 'video_urls' in vid_data:
            print(f"video_urls count: {len(vid_data['video_urls'])}")
        else:
            # Print first 500 chars of data to understand structure
            data_str = json.dumps(data.get('data', {}))
            print(f"data content (first 500 chars): {data_str[:500]}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Use base_url + extracted params
    print(f"\n--- Test 2: Reconstructed request ---")
    base_url = url.split('?')[0]
    params['_rticket'] = str(int(time.time() * 1000))
    try:
        resp = requests.get(base_url, params=params, headers=headers, timeout=15)
        print(f"Status: {resp.status_code}")
        data = resp.json()
        print(f"status_code in response: {data.get('status_code')}")
        print(f"status_msg: {data.get('status_msg', '')}")
        data_str = json.dumps(data.get('data', {}))
        print(f"data content (first 500 chars): {data_str[:500]}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Also check video_detail/v1 (POST)
    break

print(f"\n\n--- Test 3: video_detail POST ---")
for entry in har['log']['entries']:
    url = entry['request']['url']
    if 'video_detail/v1/' not in url or 'multi' in url:
        continue
    
    req = entry['request']
    headers = {h['name']: h['value'] for h in req['headers']}
    
    body_text = req.get('postData', {}).get('text', '{}')
    try:
        body = json.loads(body_text)
    except:
        body = {}
    
    print(f"URL: {url[:120]}...")
    print(f"Body: {body}")
    
    try:
        resp = requests.post(url, headers=headers, json=body, timeout=15)
        print(f"Status: {resp.status_code}")
        data = resp.json()
        print(f"status_code: {data.get('status_code')}")
        print(f"status_msg: {data.get('status_msg', '')}")
        
        vd = data.get('data', {})
        video_data = vd.get('video_data', {})
        if isinstance(video_data, dict):
            print(f"video_data keys: {list(video_data.keys())[:10]}")
            vlist = video_data.get('video_list', [])
            print(f"video_list count: {len(vlist)}")
            if vlist:
                print(f"First vid: {vlist[0].get('vid', 'N/A')}")
        else:
            data_str = json.dumps(vd)
            print(f"data (first 500 chars): {data_str[:500]}")
    except Exception as e:
        print(f"Error: {e}")
    break

print("\nDone!")
