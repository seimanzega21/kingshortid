#!/usr/bin/env python3
"""
Test API replay: call multi_video_model with captured headers 
but NEW vid IDs to see if we can fetch all episode URLs.
"""
import json, sys, io, gzip, time
import requests
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Load replay data
with open('api_replay_data.json', 'r', encoding='utf-8') as f:
    replay = json.load(f)

vm = replay['video_model']
series = replay['series']

# Pick a drama and select vids that were NOT in the original HAR video_model
# (i.e., episodes we haven't fetched yet)
# Already captured vid IDs (from HAR video_model responses)
with open('melolo1.har', 'r', encoding='utf-8') as f:
    har = json.load(f)

captured_vids = set()
for entry in har['log']['entries']:
    url = entry['request']['url']
    if 'video_model' not in url:
        continue
    mime = entry['response']['content'].get('mimeType', '')
    if 'json' not in mime:
        continue
    text = entry['response']['content'].get('text', '')
    if not text:
        continue
    try:
        data = json.loads(text)
    except:
        continue
    if isinstance(data.get('data'), dict):
        for k in data['data'].keys():
            captured_vids.add(k)

print(f"Already captured vids: {len(captured_vids)}")

# Pick first series and get uncaptured vid IDs
first_series = list(series.values())[0]
all_vids = [v['vid'] for v in first_series['vids']]
uncaptured = [v for v in all_vids if v not in captured_vids]
print(f"Series: {first_series.get('book_name', first_series['series_id'][-8:])}")
print(f"Total episodes: {first_series['total_episodes']}")
print(f"Known vids: {len(all_vids)}")
print(f"Uncaptured vids to test: {len(uncaptured)}")

if not uncaptured:
    print("All vids already captured!")
    sys.exit(0)

# Try with first 3 uncaptured vids
test_vids = uncaptured[:3]
print(f"\nTesting with vids: {test_vids}")

# Build request
url = vm['base_url']
params = dict(vm['params'])
params['_rticket'] = str(int(time.time() * 1000))

# Headers - reuse from capture
headers = {}
skip_headers = {'accept-encoding', 'content-length', 'host', 'connection', 'content-encoding'}
for k, v in vm['headers'].items():
    if k.lower() not in skip_headers:
        headers[k] = v

# User-Agent is critical
headers['user-agent'] = vm['headers'].get('user-agent', '')

# POST body - change the video_id to our test vids
post_body = {
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

print(f"\nSending POST to: {url}")
print(f"video_id: {post_body['video_id']}")

try:
    resp = requests.post(
        url,
        params=params,
        headers=headers,
        json=post_body,
        timeout=30,
    )
    
    print(f"\nResponse status: {resp.status_code}")
    print(f"Response size: {len(resp.content)} bytes")
    print(f"Content-Type: {resp.headers.get('Content-Type', 'none')}")
    
    try:
        data = resp.json()
        print(f"Response code: {data.get('code', 'N/A')}")
        print(f"Response message: {data.get('message', 'N/A')}")
        
        if 'data' in data and isinstance(data['data'], dict):
            print(f"\nGOT VIDEO DATA for {len(data['data'])} vids!")
            for vid, vinfo in data['data'].items():
                if isinstance(vinfo, dict):
                    main_url = vinfo.get('main_url', '')
                    w = vinfo.get('video_width', 0)
                    h = vinfo.get('video_height', 0)
                    print(f"  vid={vid}")
                    print(f"    URL: {main_url[:100]}...")
                    print(f"    Size: {w}x{h}")
        else:
            print(f"\nFull response: {json.dumps(data, indent=2)[:500]}")
    except:
        print(f"Raw response: {resp.text[:500]}")

except Exception as e:
    print(f"Request failed: {e}")
