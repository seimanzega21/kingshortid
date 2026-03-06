#!/usr/bin/env python3
"""Quick test: does the fixed POST call to multi_video_model actually return URLs?"""
import json, sys, io, time, requests
from pathlib import Path
from urllib.parse import urlparse, parse_qs

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stdout.reconfigure(line_buffering=True)

har_path = Path('melolo4.har')
with open(har_path, 'r', encoding='utf-8') as f:
    har = json.load(f)

# Get template
for entry in har['log']['entries']:
    url = entry['request']['url']
    if 'multi_video_model' not in url:
        continue
    
    req = entry['request']
    headers = {}
    skip = {'accept-encoding', 'content-length', 'host', 'connection', 'content-encoding'}
    for h in req['headers']:
        if h['name'].lower() not in skip:
            headers[h['name'].lower()] = h['value']
    
    parsed = urlparse(url)
    params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
    base_url = url.split('?')[0]
    
    # Get some vid IDs from video_detail
    test_vids = []
    for e2 in har['log']['entries']:
        u2 = e2['request']['url']
        if 'video_detail/v1/' not in u2 or 'multi' in u2:
            continue
        t2 = e2['response']['content'].get('text', '')
        if not t2:
            continue
        try:
            d2 = json.loads(t2)
            vd = d2.get('data', {}).get('video_data', {})
            if not vd:
                for kk, vv in d2.get('data', {}).items():
                    if isinstance(vv, dict) and 'video_data' in vv:
                        vd = vv['video_data']
                        break
            vl = vd.get('video_list', [])
            for ep in vl[:8]:
                vid = ep.get('vid')
                if vid:
                    test_vids.append(str(vid))
            if test_vids:
                break
        except:
            pass
    
    if not test_vids:
        print("No test vids found!")
        sys.exit(1)
    
    print(f"Test vids ({len(test_vids)}): {', '.join(test_vids[:3])}...")
    
    # Test 1: POST (correct method) 
    print(f"\n--- POST test (correct) ---")
    body = {
        "biz_param": {
            "detail_page_version": 0,
            "device_level": 3,
            "need_all_video_definition": True,
            "need_mp4_align": False,
            "use_os_player": False,
            "use_server_dns": False,
            "video_platform": 1024
        },
        "video_id": ",".join(test_vids)
    }
    
    params['_rticket'] = str(int(time.time() * 1000))
    
    resp = requests.post(base_url, params=params, headers=headers, json=body, timeout=15)
    print(f"Status: {resp.status_code}")
    data = resp.json()
    
    d = data.get('data', {})
    count = 0
    for vid_id, vinfo in d.items():
        if isinstance(vinfo, dict) and vinfo.get('main_url'):
            count += 1
            if count <= 2:
                print(f"  {vid_id}: {vinfo['main_url'][:80]}...")
    
    print(f"URLs found: {count}/{len(test_vids)}")
    
    if count == 0:
        print(f"\nResponse data keys: {list(d.keys())[:5]}")
        print(f"Full response (first 500 chars): {json.dumps(data)[:500]}")
    
    break

print("\nDone!")
