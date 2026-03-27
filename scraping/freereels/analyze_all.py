"""Analyze auto-crawled dramas from freereels_all_dramas.json"""
import json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Try latest file first
for fname in ['freereels_all_dramas (1).json', 'freereels_all_dramas.json']:
    path = rf'C:\Users\Seiman\Downloads\{fname}'
    try:
        with open(path) as f:
            data = json.load(f)
        print(f'File: {fname} ({len(data)} dramas)')
        break
    except:
        continue

total_eps = 0
for url, info in data.items():
    title = info.get('title', 'Unknown')
    urls_list = info.get('urls', [])
    m3u8 = [u for u in urls_list if '.m3u8' in u and 'h264' in u]
    srts = [u for u in urls_list if '.srt' in u]
    ep_count = len(m3u8)
    total_eps += ep_count
    series_key = url.split('/series/')[-1].split('/')[0].split('?')[0] if '/series/' in url else '?'
    print(f'  {ep_count:3d} eps | {title[:55]:55s} | key={series_key}')

print(f'\nTotal: {len(data)} dramas, {total_eps} episodes')
