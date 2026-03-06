#!/usr/bin/env python3
"""Find ALL cover-related fields in video_data"""
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open('melolo1.har', 'r', encoding='utf-8') as f:
    har = json.load(f)

found = 0
for entry in har['log']['entries']:
    url = entry['request']['url']
    if 'video_detail' not in url or 'video_model' in url:
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
    if not isinstance(data.get('data'), dict):
        continue
    
    for k, v in data['data'].items():
        if not isinstance(v, dict):
            continue
        vd = v.get('video_data', {})
        if not isinstance(vd, dict):
            continue
        vl = vd.get('video_list', [])
        if not vl:
            continue
        
        found += 1
        if found <= 3:
            name = vd.get('book_name', 'unknown')
            print(f"\n--- Series {k} ({name}) ---")
            # Print all fields with 'cover', 'poster', 'image', 'thumb' in name
            for field in sorted(vd.keys()):
                fl = field.lower()
                if any(x in fl for x in ['cover', 'poster', 'image', 'thumb', 'pic', 'photo']):
                    val = vd[field]
                    if isinstance(val, str) and len(val) > 5:
                        print(f"  {field}: {val[:120]}")
                    elif isinstance(val, str):
                        print(f"  {field}: (empty)")
                    else:
                        print(f"  {field}: {val}")
            
            # Also check video_list[0]
            if vl and isinstance(vl[0], dict):
                ep = vl[0]
                for field in sorted(ep.keys()):
                    fl = field.lower()
                    if any(x in fl for x in ['cover', 'poster', 'image', 'thumb']):
                        val = ep[field]
                        if isinstance(val, str) and len(val) > 5:
                            print(f"  video_list[0].{field}: {val[:120]}")

print(f"\nTotal series with video_list: {found}")
