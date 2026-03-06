import json

data = json.load(open('melolo_analysis/full_api_responses.json', 'r', encoding='utf-8'))

keywords = ['book', 'drama', 'feed', 'chapter', 'episode', 'play', 'series', 'detail', 'home', 'mall', 'recommend', 'bookmall']

print("=== DRAMA-RELATED API ENDPOINTS ===\n")
found = []
for r in data:
    url = r['url']
    if 'tmtreader' not in url:
        continue
    # Extract path
    path = url.split('tmtreader.com')[1].split('?')[0] if 'tmtreader.com' in url else ''
    if not any(k in path.lower() for k in keywords):
        continue
    found.append({'path': path, 'method': r['method'], 'data': r['data']})

for f in found:
    print(f"{f['method']:5} {f['path']}")
    d = f['data']
    if isinstance(d, dict) and 'data' in d:
        inner = d['data']
        if isinstance(inner, dict):
            print(f"      data.keys: {list(inner.keys())[:12]}")
            # Look for nested lists that contain drama data
            for k, v in inner.items():
                if isinstance(v, list) and len(v) > 0 and isinstance(v[0], dict):
                    print(f"      data.{k}[{len(v)}]: {list(v[0].keys())[:15]}")
                elif isinstance(v, dict):
                    for k2, v2 in v.items():
                        if isinstance(v2, list) and len(v2) > 0 and isinstance(v2[0], dict):
                            print(f"      data.{k}.{k2}[{len(v2)}]: {list(v2[0].keys())[:15]}")
        elif isinstance(inner, list):
            print(f"      data[{len(inner)}]")
            if inner and isinstance(inner[0], dict):
                print(f"      data[0].keys: {list(inner[0].keys())[:15]}")
    print()

# Also count important content
print(f"\nTotal drama-related endpoints: {len(found)}")
