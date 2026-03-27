"""Debug to find all episodes from flat array via episode_list chain"""
import json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('nuxt_flat.json', encoding='utf-8') as f:
    flat = json.load(f)

def resolve_scalar(val, depth=0):
    """Follow integer references in flat array until we get a non-integer."""
    if depth > 50: return val
    if isinstance(val, int) and 0 <= val < len(flat):
        return resolve_scalar(flat[val], depth + 1)
    return val

# Find which dicts have episode_list
print('=== Looking for series dict with episode_list ===')
for i, item in enumerate(flat):
    if isinstance(item, dict) and 'episode_list' in item:
        ep_list_ref = item['episode_list']
        ep_list = resolve_scalar(ep_list_ref)
        ep_list_type = type(ep_list).__name__
        ep_list_len = len(ep_list) if isinstance(ep_list, list) else '?'
        print(f'[{i}] episode_list ref={ep_list_ref} -> {ep_list_type}({ep_list_len})')

print()
print('=== Trying episode_list from index 98 ===')
item = flat[98]
ep_list_ref = item['episode_list']
ep_list = resolve_scalar(ep_list_ref)
print(f'episode_list len: {len(ep_list) if isinstance(ep_list, list) else "NOT A LIST: "+str(ep_list)[:60]}')

if isinstance(ep_list, list):
    found_eps = {}
    for ep_ref in ep_list:
        # Each ep_ref might be an int index to episode dict
        ep_dict_raw = resolve_scalar(ep_ref) if isinstance(ep_ref, int) else ep_ref
        if not isinstance(ep_dict_raw, dict):
            print(f'  ep_ref={ep_ref} -> not dict: {type(ep_dict_raw).__name__} {str(ep_dict_raw)[:40]}')
            continue

        # Resolve individual fields
        ep_idx = resolve_scalar(ep_dict_raw.get('index', 0))
        ep_ext = resolve_scalar(ep_dict_raw.get('external_audio_h264_m3u8') or 0)
        ep_m3u8 = resolve_scalar(ep_dict_raw.get('m3u8_url') or 0)
        ep_vid = resolve_scalar(ep_dict_raw.get('video_url') or 0)
        
        hls = ''
        for candidate in [ep_ext, ep_m3u8, ep_vid]:
            if isinstance(candidate, str) and candidate.startswith('http'):
                hls = candidate
                break
        
        print(f'  ep_idx={ep_idx} (type:{type(ep_idx).__name__}) hls={str(hls)[:60]}')
        
        if isinstance(ep_idx, int) and 1 <= ep_idx <= 999 and hls:
            found_eps[ep_idx] = hls

    print(f'\nValid episodes: {len(found_eps)}')
    for idx in sorted(found_eps.keys()):
        print(f'  ep{idx:03d}: {found_eps[idx][:70]}')
