"""Test with saved nuxt_flat.json - use saved data"""
import sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('nuxt_flat.json', encoding='utf-8') as f:
    flat = json.load(f)

def r1(val):
    if isinstance(val, int) and 0 <= val < len(flat):
        return flat[val]
    return val

def rstr(val):
    for _ in range(10):
        if isinstance(val, str): return val
        if isinstance(val, int) and 0 <= val < len(flat):
            val = flat[val]
        else:
            return None
    return val if isinstance(val, str) else None

def rint(val):
    resolved = r1(val)
    if isinstance(resolved, int) and 1 <= resolved <= 999:
        return resolved
    if isinstance(val, int) and 1 <= val <= 999:
        return val
    if isinstance(resolved, str):
        try: return int(resolved)
        except: pass
    return None

# Find episode_list
episodes = {}
for i, item in enumerate(flat):
    if not isinstance(item, dict): continue
    if 'episode_list' not in item: continue
    
    ep_list = r1(item['episode_list'])
    if not isinstance(ep_list, list):
        ep_list = r1(ep_list)
    if not isinstance(ep_list, list):
        continue
    
    print(f'Series dict at flat[{i}] with {len(ep_list)} episodes')
    
    for ep_ref in ep_list:
        ep_dict = r1(ep_ref)
        if not isinstance(ep_dict, dict): continue
        
        ep_num = None
        for fn in ['episode_number', 'index', 'ep_num']:
            raw = ep_dict.get(fn)
            if raw is None: continue
            resolved = rint(raw)
            if isinstance(resolved, int) and 1 <= resolved <= 999:
                ep_num = resolved
                break
        
        hls = ''
        for fn in ['external_audio_h264_m3u8', 'm3u8_url', 'video_url']:
            raw = ep_dict.get(fn)
            if raw is None: continue
            h = rstr(raw)
            if isinstance(h, str) and h.startswith('http'):
                hls = h
                break
        
        if ep_num:
            episodes[ep_num] = hls[:60] if hls else None
    
    break

print(f'\nTotal episodes found: {len(episodes)}')
for n in sorted(episodes.keys()):
    print(f'  ep{n:03d}: {episodes[n]}')
