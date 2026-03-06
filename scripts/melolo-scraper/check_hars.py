#!/usr/bin/env python3
"""Check what endpoints exist in melolo2 and melolo3 HARs"""
import json, sys, io
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

for har_name in ['melolo2.har', 'melolo3.har']:
    print(f"\n{'='*60}")
    print(f"  {har_name}")
    print(f"{'='*60}")
    
    with open(har_name, 'r', encoding='utf-8') as f:
        har = json.load(f)
    
    entries = har['log']['entries']
    print(f"Total entries: {len(entries)}")
    
    # Count by domain and endpoint
    endpoints = Counter()
    domains = Counter()
    for entry in entries:
        url = entry['request']['url']
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.hostname or ''
            path = parsed.path
            domains[domain] += 1
            if 'tmtreader' in domain or 'novel' in path or 'video' in path or 'book' in path:
                endpoints[f"{domain}{path}"] += 1
        except:
            pass
    
    print(f"\nTop domains:")
    for d, c in domains.most_common(15):
        print(f"  {c:>4}x {d}")
    
    print(f"\nRelevant API endpoints:")
    for e, c in endpoints.most_common(20):
        print(f"  {c:>4}x {e}")
    
    # Check for video_detail specifically
    vd_count = 0
    mvd_count = 0
    for entry in entries:
        url = entry['request']['url']
        if 'video_detail' in url and 'video_model' not in url:
            vd_count += 1
        if 'multi_video_detail' in url:
            mvd_count += 1
    print(f"\nvideo_detail entries: {vd_count}")
    print(f"multi_video_detail entries: {mvd_count}")
    
    # Check for any JSON responses with video data
    has_video_data = 0
    for entry in entries:
        mime = entry['response']['content'].get('mimeType', '')
        if 'json' not in mime:
            continue
        text = entry['response']['content'].get('text', '')
        if not text:
            continue
        if 'video_list' in text or 'video_data' in text:
            has_video_data += 1
    print(f"Responses containing 'video_list'/'video_data': {has_video_data}")
