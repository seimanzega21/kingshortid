#!/usr/bin/env python3
"""Debug: Find thumb_url fields in HAR bookmall responses"""
import json, sys, io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stdout.reconfigure(line_buffering=True)

har_path = Path('melolo4.har')
with open(har_path, 'r', encoding='utf-8') as f:
    har = json.load(f)

found = 0
for entry in har['log']['entries']:
    url = entry['request']['url']
    if 'bookmall/cell/change' not in url:
        continue
    
    text = entry['response']['content'].get('text', '')
    if not text:
        continue
    
    data = json.loads(text)
    
    # Explore the response structure
    if found < 1:
        print(f"\n=== bookmall response keys ===")
        print(f"Top keys: {list(data.keys())}")
        d = data.get('data', {})
        print(f"data keys: {list(d.keys())[:10]}")
        
        # Find where books/thumb_urls live
        def find_thumb(obj, path=""):
            if isinstance(obj, dict):
                if 'thumb_url' in obj:
                    print(f"  FOUND thumb_url at {path}")
                    print(f"    title: {obj.get('book_name', obj.get('title', '?'))}")
                    print(f"    thumb: {obj['thumb_url'][:80]}...")
                    return True
                for k, v in obj.items():
                    if find_thumb(v, f"{path}.{k}"):
                        return True
            elif isinstance(obj, list):
                for i, item in enumerate(obj[:3]):
                    if find_thumb(item, f"{path}[{i}]"):
                        return True
            return False
        
        find_thumb(data, "root")
        
        # Also dump first level of data structure
        for k, v in d.items():
            if isinstance(v, list):
                print(f"  data.{k}: list[{len(v)}]")
                if v and isinstance(v[0], dict):
                    print(f"    first item keys: {list(v[0].keys())[:10]}")
            elif isinstance(v, dict):
                print(f"  data.{k}: dict keys={list(v.keys())[:5]}")
            else:
                print(f"  data.{k}: {type(v).__name__} = {str(v)[:50]}")
    
    found += 1

print(f"\nTotal bookmall responses: {found}")
