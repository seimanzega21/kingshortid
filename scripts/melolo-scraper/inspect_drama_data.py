import json

data = json.load(open('melolo_analysis/full_api_responses.json', 'r', encoding='utf-8'))

# Find bookmall/feed endpoints with actual drama data
print("=== LOOKING FOR DRAMA FEED DATA ===\n")
for i, r in enumerate(data):
    url = r['url']
    if 'tmtreader' not in url:
        continue
    path = url.split('tmtreader.com')[1].split('?')[0]
    d = r['data']
    
    if not isinstance(d, dict) or 'data' not in d:
        continue
    inner = d['data']
    if not isinstance(inner, dict):
        continue
    
    # Look for cells, books, items that have drama-like data
    for key in ['cells', 'books', 'items', 'data_list', 'book_list', 'series_list']:
        if key in inner and isinstance(inner[key], list) and len(inner[key]) > 0:
            item = inner[key][0]
            if isinstance(item, dict):
                # Check if it has drama-like keys
                item_keys = list(item.keys())
                if any(k in str(item_keys) for k in ['book', 'title', 'name', 'cover', 'episode', 'chapter', 'drama', 'series']):
                    print(f"[{i}] {path}")
                    print(f"  {key}: {len(inner[key])} items")
                    print(f"  Keys: {item_keys[:20]}")
                    # Show first item sample
                    sample = json.dumps(item, ensure_ascii=False)[:600]
                    print(f"  Sample: {sample}\n")

print("\n=== LOOKING FOR VIDEO MODEL ENDPOINTS ===\n")
for i, r in enumerate(data):
    url = r['url']
    if 'multi_video_model' in url or 'player' in url or 'play_url' in url:
        path = url.split('tmtreader.com')[1].split('?')[0] if 'tmtreader.com' in url else url[:100]
        d = r['data']
        print(f"[{i}] {path}")
        if isinstance(d, dict):
            print(f"  Keys: {list(d.keys())[:15]}")
            if 'data' in d:
                inner = d['data']
                if isinstance(inner, dict):
                    print(f"  data.keys: {list(inner.keys())[:15]}")
                    for k, v in inner.items():
                        if isinstance(v, dict) and ('play_url' in str(v) or 'video' in str(v)):
                            sample = json.dumps(v, ensure_ascii=False)[:400]
                            print(f"  data.{k}: {sample}")
                elif isinstance(inner, list):
                    print(f"  data[{len(inner)}]")
                    if inner and isinstance(inner[0], dict):
                        print(f"  data[0].keys: {list(inner[0].keys())[:15]}")
                        sample = json.dumps(inner[0], ensure_ascii=False)[:500]
                        print(f"  data[0]: {sample}")
        print()
