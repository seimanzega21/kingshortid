#!/usr/bin/env python3
"""Full inspection of video_data structure in melolo2/3"""
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

for har_name in ['melolo2.har', 'melolo3.har']:
    print(f"\n{'='*60}")
    print(f"  {har_name}")
    print(f"{'='*60}")
    
    with open(har_name, 'r', encoding='utf-8') as f:
        har = json.load(f)
    
    seen = 0
    for entry in har['log']['entries']:
        url = entry['request']['url']
        if 'video_detail' not in url or 'video_model' in url:
            continue
        text = entry['response']['content'].get('text', '')
        if not text:
            continue
        try:
            data = json.loads(text)
        except:
            continue
        
        vd = data.get('data', {}).get('video_data', {})
        if not isinstance(vd, dict):
            continue
        
        seen += 1
        if seen > 2:
            continue
        
        print(f"\n--- Entry {seen} ---")
        print(f"  ALL video_data keys ({len(vd)} total):")
        for k in sorted(vd.keys()):
            v = vd[k]
            if isinstance(v, list):
                print(f"    {k}: list[{len(v)}]")
                if v and isinstance(v[0], dict):
                    print(f"      [0] keys: {list(v[0].keys())[:10]}")
                    if v[0].get('vid'):
                        print(f"      [0].vid = {v[0]['vid']}")
            elif isinstance(v, dict):
                print(f"    {k}: dict keys={list(v.keys())[:8]}")
            elif isinstance(v, str) and len(v) > 100:
                print(f"    {k}: '{v[:80]}...'")
            else:
                print(f"    {k}: {v}")
        
        # Check series_id
        series_id = vd.get('series_id', '')
        book_name = vd.get('book_name', '')
        video_list = vd.get('video_list', [])
        cover = vd.get('series_cover', '')
        total_ep = vd.get('total_episode', 0)
        print(f"\n  series_id: {series_id}")
        print(f"  book_name: {book_name[:50]}")
        print(f"  video_list: {len(video_list)} items")
        print(f"  total_episode: {total_ep}")
        print(f"  series_cover: {cover[:80]}..." if cover else "  series_cover: N/A")
    
    print(f"\n  Total video_detail entries: {seen}")
