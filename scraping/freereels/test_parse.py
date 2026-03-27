"""Quick test for episode parsing"""
import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from freereels_full_eps import fetch_episode_list

key = 'h7XYuJo63T'
eps = fetch_episode_list(key)
print(f'Found: {len(eps)} episodes')
for ep in eps[:5]:
    idx = ep.get('index', '?')
    hls = str(ep.get('hls', ''))[:70]
    sub = str(ep.get('sub_srt', '') or ep.get('sub_vtt', ''))[:50]
    sub = sub if sub else '(none)'
    print(f'  ep{idx}: {hls}')
    print(f'    sub: {sub}')
