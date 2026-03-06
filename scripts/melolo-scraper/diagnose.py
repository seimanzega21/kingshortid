#!/usr/bin/env python3
"""Full diagnosis of all drama folders — check title, cover, episodes, metadata"""
import json, sys, io, os
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

r2_dir = Path('r2_ready/melolo')
dramas = sorted(r2_dir.iterdir())

print("=" * 80)
print("  FULL DIAGNOSIS OF ALL DRAMA FOLDERS")
print("=" * 80)

zero_ep = []
partial = []
missing_cover = []
missing_title = []

for d in dramas:
    if not d.is_dir():
        continue
    
    meta_path = d / 'metadata.json'
    cover_path = d / 'cover.jpg'
    eps_dir = d / 'episodes'
    
    # Count episodes
    ep_count = 0
    if eps_dir.exists():
        ep_count = len([x for x in eps_dir.iterdir() if x.is_dir()])
    
    # Read metadata
    meta = {}
    if meta_path.exists():
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
    
    title = meta.get('title', '')
    series_id = meta.get('series_id', '')
    total_eps = meta.get('total_episodes', 0)
    description = meta.get('description', '')
    cover_field = meta.get('cover', '')
    
    has_cover = cover_path.exists() and cover_path.stat().st_size > 100
    
    folder_name = d.name
    
    # Identify issues
    issues = []
    if not title or title.startswith('Drama '):
        issues.append('NO_TITLE')
        missing_title.append(folder_name)
    if not has_cover:
        issues.append('NO_COVER')
        missing_cover.append(folder_name)
    if ep_count == 0:
        issues.append('ZERO_EPISODES')
        zero_ep.append(folder_name)
    elif total_eps > 0 and ep_count < total_eps * 0.8:
        issues.append(f'PARTIAL({ep_count}/{total_eps})')
        partial.append(folder_name)
    
    if issues:
        print(f"\n{'─'*60}")
        print(f"  📂 {folder_name}")
        print(f"  Title: {title or '(empty)'}")
        print(f"  Series ID: {series_id}")
        print(f"  Episodes: {ep_count}/{total_eps}")
        print(f"  Cover: {'✅' if has_cover else '❌'}")
        print(f"  Description: {description[:80]}..." if description else f"  Description: (empty)")
        print(f"  Issues: {', '.join(issues)}")

print(f"\n{'='*80}")
print(f"  SUMMARY")
print(f"{'='*80}")
print(f"Total folders: {len(dramas)}")
print(f"Missing title: {len(missing_title)} → {missing_title}")
print(f"Missing cover: {len(missing_cover)} → {missing_cover}")
print(f"Zero episodes: {len(zero_ep)} → {zero_ep}")
print(f"Partial episodes: {len(partial)} → {partial}")

# Check if any cover URLs exist in metadata for dramas missing covers
print(f"\n{'='*80}")
print(f"  COVER URLs FOR DRAMAS WITHOUT COVERS")
print(f"{'='*80}")
for d in dramas:
    if not d.is_dir():
        continue
    cover_path = d / 'cover.jpg'
    if cover_path.exists() and cover_path.stat().st_size > 100:
        continue
    meta_path = d / 'metadata.json'
    if meta_path.exists():
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        # Check if there's a cover URL we can try
        print(f"  {d.name}: cover field='{meta.get('cover', '')}', desc='{meta.get('description', '')[:50]}'")

# Also check HAR for cover URLs for these series
print(f"\n{'='*80}")
print(f"  SEARCHING HAR FOR MISSING COVER URLs")
print(f"{'='*80}")

# Get series_ids of dramas without covers
missing_cover_ids = set()
for d in dramas:
    if not d.is_dir():
        continue
    cover_path = d / 'cover.jpg'
    if cover_path.exists() and cover_path.stat().st_size > 100:
        continue
    meta_path = d / 'metadata.json'
    if meta_path.exists():
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        sid = meta.get('series_id', '')
        if sid:
            missing_cover_ids.add(sid)

# Search all HARs for these series_ids and their covers
for har_name in ['melolo1.har', 'melolo2.har', 'melolo3.har']:
    if not Path(har_name).exists():
        continue
    with open(har_name, 'r', encoding='utf-8') as f:
        har = json.load(f)
    
    for entry in har['log']['entries']:
        url = entry['request']['url']
        if 'video_detail' not in url:
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
        
        d = data['data']
        # Check both formats
        vd_list = []
        if 'video_data' in d and isinstance(d['video_data'], dict):
            vd = d['video_data']
            sid = str(vd.get('series_id', '') or vd.get('series_id_str', ''))
            vd_list.append((sid, vd))
        else:
            for k, v in d.items():
                if isinstance(v, dict) and isinstance(v.get('video_data'), dict):
                    vd_list.append((k, v['video_data']))
        
        for sid, vd in vd_list:
            if sid in missing_cover_ids:
                cover = vd.get('series_cover', '')
                title = vd.get('series_title', '') or vd.get('book_name', '')
                print(f"  Found cover for {sid}: {cover[:80]}..." if cover else f"  NO cover for {sid}")
                print(f"    Title: {title}")
