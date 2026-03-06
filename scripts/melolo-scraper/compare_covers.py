#!/usr/bin/env python3
"""Download and compare all cover sources"""
import json, sys, io, subprocess
import requests
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

outdir = Path('cover_comparison')
outdir.mkdir(exist_ok=True)

with open('melolo1.har', 'r', encoding='utf-8') as f:
    har = json.load(f)

# Find all cover URLs for the first drama
target = '7423711830746336272'  # aka drama-74912517

covers = {}

# 1. From video_detail
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
    
    if target in data['data']:
        vd = data['data'][target].get('video_data', {})
        covers['series_cover'] = vd.get('series_cover', '')
        vl = vd.get('video_list', [])
        if vl and isinstance(vl[0], dict):
            covers['video_list_cover'] = vl[0].get('cover', '')
            covers['episode_cover'] = vl[0].get('episode_cover', '')
        break

# 2. From bookshelf
for entry in har['log']['entries']:
    url = entry['request']['url']
    if 'bookshelf' not in url and 'book_history' not in url:
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
    
    # Search for thumb_url
    items = []
    if isinstance(data.get('data'), dict):
        items.extend(data['data'].get('shelf_infos', []))
        items.extend(data['data'].get('data_list', []))
    for item in items:
        bi = item.get('book_info', item)
        thumb = bi.get('thumb_url', '')
        if thumb:
            covers['bookshelf_thumb'] = thumb
            break
    if 'bookshelf_thumb' in covers:
        break

print("Found cover URLs:")
for name, url in covers.items():
    print(f"  {name}:")
    print(f"    {url[:150]}")
    print()

# Download each one
for name, url in covers.items():
    if not url:
        continue
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        raw_path = outdir / f"{name}.heic"
        jpg_path = outdir / f"{name}.jpg"
        with open(raw_path, 'wb') as f:
            f.write(resp.content)
        
        # Convert HEIC to JPG
        result = subprocess.run(
            ['ffmpeg', '-y', '-i', str(raw_path), '-q:v', '2', str(jpg_path)],
            capture_output=True, timeout=30
        )
        if result.returncode == 0:
            raw_path.unlink(missing_ok=True)
            size = jpg_path.stat().st_size
            print(f"  Downloaded {name}: {size/1024:.0f}KB -> {jpg_path}")
        else:
            print(f"  ffmpeg failed for {name}: {result.stderr[:200]}")
            raw_path.rename(jpg_path)
    except Exception as e:
        print(f"  Failed {name}: {e}")
