"""Debug NUXT_DATA to find all episodes"""
import sys, json, re, requests
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

H5_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 11; Mobile) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'id-ID,id;q=0.9',
    'Referer': 'https://m.mydramawave.com/',
}

# rwcCi67MwS = Seorang Ibu (24 eps)
# VfjJTqZGw1 = Love Until It Hurts (88 eps)
series_key = 'rwcCi67MwS'
url = f'https://m.mydramawave.com/series/{series_key}'

print(f'Fetching: {url}')
r = requests.get(url, headers=H5_HEADERS, timeout=30)
html = r.text
print(f'HTML size: {len(html):,} bytes')

# Extract __NUXT_DATA__
m = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
if not m:
    print('ERROR: __NUXT_DATA__ not found!')
    sys.exit(1)

nuxt_raw = m.group(1).strip()
flat = json.loads(nuxt_raw)
print(f'Flat array length: {len(flat)} elements')

# Save raw flat array to file for inspection
with open('nuxt_flat.json', 'w', encoding='utf-8') as f:
    json.dump(flat, f, ensure_ascii=False, indent=2)
print('Saved flat array to nuxt_flat.json')

# Count different types
types = {}
for item in flat:
    t = type(item).__name__
    types[t] = types.get(t, 0) + 1
print('Type distribution:', types)

# Look for keys that contain 'episode' or 'm3u8' or 'video_url' as dict keys
print('\nSearching for episode-related keys in dicts...')
ep_related_indices = []
for i, item in enumerate(flat):
    if isinstance(item, dict):
        keys = set(item.keys())
        relevant = keys & {'m3u8_url', 'external_audio_h264_m3u8', 'video_url', 'episode_list', 'episode_number'}
        if relevant:
            ep_related_indices.append(i)
            print(f'  [{i}] keys: {sorted(item.keys())}')
            # show a few values
            for k in list(item.keys())[:5]:
                print(f'       {k}: {str(item[k])[:60]}')

print(f'\nTotal ep-related dicts: {len(ep_related_indices)}')

# Look for 'episode_list' key
print('\nSearching for episode_list key...')
for i, item in enumerate(flat):
    if isinstance(item, dict) and 'episode_list' in item:
        ep_list_val = item['episode_list']
        print(f'  [{i}] episode_list type: {type(ep_list_val).__name__}, value: {str(ep_list_val)[:100]}')

# Try resolving episode_list
def resolve(val, depth=0, visited=None):
    if visited is None: visited = set()
    if depth > 30: return val
    if isinstance(val, int):
        if val < 0 or val >= len(flat): return val
        if val in visited: return val
        visited = visited | {val}
        return resolve(flat[val], depth + 1, visited)
    if isinstance(val, list):
        return [resolve(v, depth + 1, visited) for v in val]
    if isinstance(val, dict):
        return {k: resolve(v, depth + 1, visited) for k, v in val.items()}
    return val

print('\nTrying to resolve episode_list...')
for i, item in enumerate(flat):
    if isinstance(item, dict) and 'episode_list' in item:
        resolved_ep_list = resolve(item['episode_list'])
        if isinstance(resolved_ep_list, list):
            print(f'  [{i}] episode_list: {len(resolved_ep_list)} items')
            # Check first item
            for ep in resolved_ep_list[:3]:
                if isinstance(ep, dict):
                    ep_keys = list(ep.keys())
                    print(f'    ep keys: {ep_keys}')
                    if 'm3u8_url' in ep or 'external_audio_h264_m3u8' in ep:
                        print(f'    m3u8_url: {str(ep.get("m3u8_url","") or ep.get("external_audio_h264_m3u8",""))[:80]}')
                        print(f'    index: {ep.get("index")} ep_num: {ep.get("episode_number")}')
                else:
                    print(f'    ep: {str(ep)[:60]}')
