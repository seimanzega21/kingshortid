"""Deep inspect of episode dicts in flat array to understand structure"""
import json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('nuxt_flat.json', encoding='utf-8') as f:
    flat = json.load(f)

# flat[112] = list of 24 episode indices
ep_refs = flat[112]
print(f'Episode refs: {ep_refs[:5]}...')
print()

# Inspect first episode
first_ep_idx = ep_refs[0]  # e.g. 113
print(f'First ep at flat[{first_ep_idx}]:')
first_ep = flat[first_ep_idx]
print(f'  Type: {type(first_ep).__name__}')
if isinstance(first_ep, dict):
    for k, v in list(first_ep.items())[:20]:
        vtype = type(v).__name__
        vpreview = str(v)[:80]
        # If int, show what it resolves to
        if isinstance(v, int) and 0 <= v < len(flat):
            resolved = flat[v]
            vresolved = str(resolved)[:60]
            print(f'  {k}: {v} -> {vresolved}')
        else:
            print(f'  {k}: [{vtype}] {vpreview}')

print()
print('=== All episodes quick scan ===')
for ep_ref in ep_refs:
    ep = flat[ep_ref]
    if not isinstance(ep, dict):
        print(f'  flat[{ep_ref}] = {type(ep).__name__}: {str(ep)[:40]}')
        continue
    
    # Find episode number
    ep_num = None
    for k in ['episode_number', 'index', 'ep', 'no', 'num', 'ep_num']:
        if k in ep:
            v = ep[k]
            # try to resolve if int
            if isinstance(v, int) and 0 <= v < len(flat):
                resolved = flat[v]
                if isinstance(resolved, int) or (isinstance(resolved, str) and resolved.isdigit()):
                    ep_num = resolved if isinstance(resolved, int) else int(resolved)
                elif isinstance(resolved, str) and len(resolved) < 5 and not resolved.startswith('http'):
                    try: ep_num = int(resolved)
                    except: pass
                elif isinstance(v, int) and 1 <= v <= 500:
                    # The integer itself might be the episode number
                    ep_num = v
            elif isinstance(v, (int, float)) and 1 <= v <= 500:
                ep_num = int(v)
            if ep_num: break
    
    # Find HLS
    hls = None
    for k in ['external_audio_h264_m3u8', 'm3u8_url', 'video_url', 'play_url']:
        if k in ep:
            v = ep[k]
            if isinstance(v, int) and 0 <= v < len(flat):
                resolved = flat[v]
                if isinstance(resolved, str) and resolved.startswith('http'):
                    hls = resolved
                    break
            elif isinstance(v, str) and v.startswith('http'):
                hls = v
                break
    
    print(f'  flat[{ep_ref}]: ep_num={ep_num} hls={str(hls)[:60] if hls else None}')
