"""Debug new parser - check episode_number field resolution"""
import sys, json, re, requests
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

H5_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 11; Mobile) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'id-ID,id;q=0.9',
    'Referer': 'https://m.mydramawave.com/',
}

# Use saved flat array from debug (rwcCi67MwS - 24 episodes)
with open('nuxt_flat.json', encoding='utf-8') as f:
    flat = json.load(f)

print(f'Flat array size: {len(flat)}')

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
    for _ in range(5):
        if isinstance(val, int) and val > 999:
            if 0 <= val < len(flat):
                val = flat[val]
            else:
                return None
        elif isinstance(val, int):
            return val
        elif isinstance(val, str):
            try: return int(val)
            except: return None
        else:
            return None
    return None

# Find episode_list
print('\n=== Finding series dict with episode_list ===')
for i, item in enumerate(flat):
    if not isinstance(item, dict): continue
    if 'episode_list' not in item: continue
    
    ep_list_ref = item['episode_list']
    ep_list = r1(ep_list_ref)
    if not isinstance(ep_list, list):
        ep_list = r1(ep_list)
    if not isinstance(ep_list, list):
        continue
    
    print(f'Series dict at flat[{i}], episode_list ref={ep_list_ref} -> list of {len(ep_list)} episodes')
    
    for ep_ref in ep_list[:5]:  # First 5 episodes
        ep_dict = r1(ep_ref)
        if not isinstance(ep_dict, dict):
            print(f'  ep_ref={ep_ref} is not dict: {type(ep_dict).__name__}')
            continue
        
        print(f'\n  flat[{ep_ref}] keys: {list(ep_dict.keys())}')
        
        # Check each numeric field
        for k in ['episode_number', 'index', 'm3u8_url', 'external_audio_h264_m3u8', 'video_url']:
            raw = ep_dict.get(k)
            if raw is None: continue
            resolved_r1 = r1(raw)
            resolved_rstr = rstr(raw)
            resolved_rint = rint(raw)
            print(f'  {k}: raw={raw} r1={str(resolved_r1)[:40]} rstr={str(resolved_rstr)[:40]} rint={resolved_rint}')
    
    print('\n=== All episodes ep_num and hls ===')
    for ep_ref in ep_list:
        ep_dict = r1(ep_ref)
        if not isinstance(ep_dict, dict): continue
        
        ep_num = rint(ep_dict.get('episode_number') or ep_dict.get('index', 0))
        hls = None
        for fn in ['external_audio_h264_m3u8', 'm3u8_url', 'video_url']:
            raw = ep_dict.get(fn)
            h = rstr(raw)
            if isinstance(h, str) and h.startswith('http'):
                hls = h
                break
        print(f'  ep_num={ep_num} hls={str(hls)[:60] if hls else None}')
    
    break  # Only first series dict
