#!/usr/bin/env python3
"""Debug: comprehensive check of all video_detail responses"""
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open('melolo1.har', 'r', encoding='utf-8') as f:
    har = json.load(f)

# Collect all video_model response keys
vm_keys = set()
vm_data = {}
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
    if 'data' not in data:
        continue
    for k, v in data['data'].items():
        if isinstance(v, dict) and 'main_url' in v:
            vm_keys.add(str(k))
            vm_data[str(k)] = v

print(f"video_model: {len(vm_keys)} unique video IDs with URLs\n")

# Check ALL video_detail responses
detail_count = 0
detail_with_vlist = 0
total_vlist_items = 0
vid_mapping = {}  # vid -> (book_id, order)

for entry in har['log']['entries']:
    url = entry['request']['url']
    if 'video_detail' not in url:
        continue
    if 'video_model' in url:
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
    if 'data' not in data or not isinstance(data['data'], dict):
        continue
    
    detail_count += 1
    
    for k, v in data['data'].items():
        if not isinstance(v, dict):
            continue
        
        vd = v.get('video_data', {})
        if not isinstance(vd, dict):
            continue
        
        book_id = vd.get('book_id', '')
        book_name = vd.get('book_name', '')
        video_list = vd.get('video_list', [])
        
        if video_list:
            detail_with_vlist += 1
            total_vlist_items += len(video_list)
            
            if detail_count <= 5 or (book_name and video_list):
                print(f"--- Entry {detail_count}, key={k} ---")
                print(f"  book_id={book_id}, book_name={str(book_name)[:50]}")
                print(f"  video_list: {len(video_list)} items")
                
                # Check type of video_list items
                if video_list:
                    first = video_list[0]
                    print(f"  item type: {type(first).__name__}")
                    if isinstance(first, dict):
                        print(f"  item keys: {sorted(first.keys())}")
                        # Check if any field matches vm_keys
                        for fk, fv in first.items():
                            if str(fv) in vm_keys:
                                print(f"  ** MATCH: field '{fk}' value '{fv}' found in video_model!")
                        # Show first 2 items compactly
                        for i, item in enumerate(video_list[:2]):
                            compact = {ik: (str(iv)[:50] + '...' if isinstance(iv, str) and len(iv) > 50 else iv) for ik, iv in item.items()}
                            print(f"  [{i}]: {compact}")
                    elif isinstance(first, (str, int)):
                        matches = sum(1 for x in video_list if str(x) in vm_keys)
                        print(f"  Matches in video_model: {matches}/{len(video_list)}")
                        print(f"  Sample: {video_list[:5]}")
                print()

# Also check if video_detail entries have 'item_id' at the top level
print(f"\n=== Summary ===")
print(f"video_detail entries: {detail_count}")
print(f"Entries with video_list: {detail_with_vlist}")
print(f"Total video_list items: {total_vlist_items}")
print(f"Vid mappings collected: {len(vid_mapping)}")
