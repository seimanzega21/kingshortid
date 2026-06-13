# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests
import json
import warnings
warnings.filterwarnings('ignore')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://vidrama.asia/',
}

upstream_id = '160000641860'

# Fetch metadata
meta_url = f'https://vidrama.asia/api/idrama2/drama/{upstream_id}?lang=id'
r = requests.get(meta_url, headers=HEADERS, verify=False, timeout=20)
meta = r.json()
print(f"Title: {meta.get('short_play_name')}")
print(f"Total EP: {meta.get('current_count')}")
print()

# Check episode 1 unlock info
unlock_url = f'https://vidrama.asia/api/idrama2/unlock/{upstream_id}/1?lang=id'
r2 = requests.get(unlock_url, headers=HEADERS, verify=False, timeout=20)
data = r2.json()
ep_info = data.get('target_ep_info', {})

print("=== EP 1 UNLOCK FULL KEYS ===")
print(list(ep_info.keys()))
print()

sub_lists = []
if 'screentext_list' in ep_info:
    sub_lists.extend(ep_info['screentext_list'])
    print(f"screentext_list count: {len(ep_info['screentext_list'])}")
if 'subtitle_list' in ep_info:
    sub_lists.extend(ep_info['subtitle_list'])
    print(f"subtitle_list count: {len(ep_info['subtitle_list'])}")

print()
print("=== ALL SUBTITLE ENTRIES ===")
for s in sub_lists:
    print(f"  lang={s.get('language')} | url={s.get('url', 'N/A')[:80]}")

print()
print(f"Play URL: {ep_info.get('play_url', 'N/A')[:80]}")
