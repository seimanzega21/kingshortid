#!/usr/bin/env python3
"""Check if video_detail contains direct video URLs, bypassing multi_video_model"""
import json, sys, io, time, requests, base64
from pathlib import Path
from urllib.parse import urlparse, parse_qs

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stdout.reconfigure(line_buffering=True)

har_path = Path('melolo4.har')
with open(har_path, 'r', encoding='utf-8') as f:
    har = json.load(f)

# 1. Check video_detail HAR response structure
print("=" * 60)
print("  video_detail RESPONSE STRUCTURE (from HAR)")
print("=" * 60)

for entry in har['log']['entries']:
    url = entry['request']['url']
    if 'video_detail/v1/' not in url or 'multi' in url:
        continue
    
    text = entry['response']['content'].get('text', '')
    if not text:
        continue
    
    try:
        data = json.loads(text)
    except:
        continue
    
    d = data.get('data', {})
    vd = d.get('video_data', {})
    
    if not vd:
        # Try nested
        for k, v in d.items():
            if isinstance(v, dict) and 'video_data' in v:
                vd = v['video_data']
                break
    
    if not vd:
        print(f"  No video_data found")
        print(f"  data keys: {list(d.keys())[:15]}")
        continue
    
    print(f"  video_data keys: {list(vd.keys())[:15]}")
    
    vlist = vd.get('video_list', [])
    print(f"  video_list count: {len(vlist)}")
    
    if vlist and isinstance(vlist[0], dict):
        ep = vlist[0]
        print(f"\n  First episode keys: {list(ep.keys())}")
        print(f"    vid: {ep.get('vid', 'N/A')}")
        print(f"    title: {ep.get('title', ep.get('episode_name', 'N/A'))}")
        
        # Check for direct video URL
        for key in ['video_url', 'play_url', 'url', 'main_url', 'backup_url', 'download_url', 'mp4_url']:
            if key in ep:
                print(f"    {key}: {str(ep[key])[:100]}...")
        
        # Check play_addr
        if 'play_addr' in ep:
            pa = ep['play_addr']
            print(f"    play_addr type: {type(pa).__name__}")
            if isinstance(pa, dict):
                print(f"    play_addr keys: {list(pa.keys())}")
                if 'url_list' in pa:
                    for u in pa['url_list'][:2]:
                        print(f"      url: {u[:100]}...")
        
        # Check video
        if 'video' in ep:
            v = ep['video']
            print(f"    video type: {type(v).__name__}")
            if isinstance(v, dict):
                print(f"    video keys: {list(v.keys())[:15]}")
                for key in ['play_addr', 'download_addr', 'url']:
                    if key in v:
                        val = v[key]
                        if isinstance(val, dict) and 'url_list' in val:
                            for u in val['url_list'][:2]:
                                print(f"      video.{key}.url_list: {u[:100]}...")
                        elif isinstance(val, str):
                            print(f"      video.{key}: {val[:100]}...")
        
        # Also check all string values for URLs
        print(f"\n    All string values containing 'http' or 'cdn':")
        for k, v in ep.items():
            if isinstance(v, str) and ('http' in v or 'cdn' in v):
                print(f"      {k}: {v[:100]}...")
    break

# 2. Now test LIVE video_detail call
print(f"\n\n{'=' * 60}")
print("  LIVE video_detail CALL")
print("=" * 60)

for entry in har['log']['entries']:
    url = entry['request']['url']
    if 'video_detail/v1/' not in url or 'multi' in url:
        continue
    
    req = entry['request']
    headers = {h['name']: h['value'] for h in req['headers']}
    parsed = urlparse(url)
    params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
    
    body_text = req.get('postData', {}).get('text', '{}')
    try:
        body = json.loads(body_text)
    except:
        body = {}
    
    print(f"  series_id in body: {body.get('series_id', 'N/A')}")
    
    # Update timestamp
    params['_rticket'] = str(int(time.time() * 1000))
    
    base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    
    resp = requests.post(base_url, params=params, headers=headers, json=body, timeout=15)
    print(f"  Status: {resp.status_code}")
    
    data = resp.json()
    print(f"  status_code: {data.get('status_code')}")
    
    d = data.get('data', {})
    vd = d.get('video_data', {})
    if not vd:
        for k, v in d.items():
            if isinstance(v, dict) and 'video_data' in v:
                vd = v['video_data']
                break
    
    if vd:
        vlist = vd.get('video_list', [])
        print(f"  video_list count: {len(vlist)}")
        
        if vlist:
            ep = vlist[0]
            print(f"  First ep vid: {ep.get('vid', 'N/A')}")
            
            # Check for URLs
            for k, v in ep.items():
                if isinstance(v, str) and ('http' in v or 'cdn' in v):
                    print(f"    {k}: {v[:100]}...")
                elif isinstance(v, dict):
                    for kk, vv in v.items():
                        if isinstance(vv, str) and 'http' in vv:
                            print(f"    {k}.{kk}: {vv[:100]}...")
                        elif isinstance(vv, list) and vv and isinstance(vv[0], str) and 'http' in vv[0]:
                            print(f"    {k}.{kk}[0]: {vv[0][:100]}...")
    else:
        print(f"  No video_data!")
        raw = json.dumps(d)
        print(f"  data: {raw[:500]}")
    break

# 3. Check multi_video_detail (different endpoint)
print(f"\n\n{'=' * 60}")
print("  multi_video_detail RESPONSE STRUCTURE (from HAR)")
print("=" * 60)

for entry in har['log']['entries']:
    url = entry['request']['url']
    if 'multi_video_detail' not in url:
        continue
    
    print(f"  URL: {url[:100]}...")
    
    text = entry['response']['content'].get('text', '')
    if not text:
        print(f"  No response text")
        continue
    
    try:
        data = json.loads(text)
    except:
        print(f"  JSON parse error")
        continue
    
    d = data.get('data', {})
    print(f"  data keys: {list(d.keys())[:10]}")
    
    for k, v in list(d.items())[:2]:
        if isinstance(v, dict):
            vd = v.get('video_data', {})
            if isinstance(vd, dict):
                vl = vd.get('video_list', [])
                print(f"  {k}: video_list count={len(vl)}")
                if vl and isinstance(vl[0], dict):
                    ep = vl[0]
                    for ek, ev in ep.items():
                        if isinstance(ev, str) and 'http' in ev:
                            print(f"    {ek}: {ev[:100]}...")
    break

print("\nDone!")
