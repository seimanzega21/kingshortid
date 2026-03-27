"""Check why episodes 11+ have no HLS URL"""
import json, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('nuxt_flat.json', encoding='utf-8') as f:
    flat = json.load(f)

# flat[112] = list of 24 episode indices
ep_refs = flat[112]

# Check ep11 (index 10 in list = ep_ref for ep11)
print('=== Comparing ep1 vs ep11 in detail ===')
for ep_seq in [0, 10, 20]:  # ep1, ep11, ep21
    ep_ref = ep_refs[ep_seq]
    ep = flat[ep_ref]
    print(f'\n--- flat[{ep_ref}] (ep sequence {ep_seq+1}) ---')
    for k, v in ep.items():
        if isinstance(v, int) and 0 <= v < len(flat):
            resolved = flat[v]
            if isinstance(resolved, str):
                print(f'  {k}: {v} -> "{resolved[:80]}"')
            elif isinstance(resolved, (int, float, bool, type(None))):
                print(f'  {k}: {v} -> {resolved}')
            elif isinstance(resolved, list):
                print(f'  {k}: {v} -> list({len(resolved)}): {str(resolved[:3])[:60]}')
            elif isinstance(resolved, dict):
                print(f'  {k}: {v} -> dict keys: {list(resolved.keys())[:5]}')
        elif isinstance(v, str):
            print(f'  {k}: "{v[:80]}"')
        elif isinstance(v, (int, float, bool, type(None))):
            print(f'  {k}: {v}')
        else:
            print(f'  {k}: [{type(v).__name__}]')
