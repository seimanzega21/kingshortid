"""Find cover URLs for dubbing dramas from FreeReels data sources"""
import json, sys, os, glob
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Check freereels_series_ids.json for cover data
ids = json.loads(open(r'd:\kingshortid\scraping\freereels\freereels_series_ids.json', encoding='utf-8').read())
print(f'freereels_series_ids.json: {len(ids)} entries')
if isinstance(ids, dict):
    # Show first entry fully
    first_key = list(ids.keys())[0]
    first = ids[first_key]
    print(f'First entry keys: {list(first.keys()) if isinstance(first, dict) else type(first).__name__}')
    if isinstance(first, dict):
        print(json.dumps(first, ensure_ascii=False, indent=2)[:300])

# Check drama_info_full.json for cover data
for f in ['drama_info_full.json', 'drama_info_found.json', 'drama_info_hit.json']:
    fp = os.path.join(r'd:\kingshortid\scraping\freereels', f)
    if os.path.exists(fp):
        data = json.loads(open(fp, encoding='utf-8').read())
        print(f'\n{f}: type={type(data).__name__} len={len(data)}')
        if isinstance(data, list) and data:
            item = data[0]
            print(f'First entry keys: {list(item.keys())[:15]}')
            if 'cover' in item:
                print(f'  cover: {item["cover"][:100]}')
        elif isinstance(data, dict):
            first_key = list(data.keys())[0]
            item = data[first_key]
            if isinstance(item, dict):
                print(f'First entry keys: {list(item.keys())[:15]}')
                if 'cover' in item:
                    print(f'  cover: {item["cover"][:100]}')

# Check tab_feed for covers
for f in ['tab_feed.json', 'tab514_all_dramas.json']:
    fp = os.path.join(r'd:\kingshortid\scraping\freereels', f)
    if os.path.exists(fp):
        data = json.loads(open(fp, encoding='utf-8').read())
        print(f'\n{f}: type={type(data).__name__} len={len(data)}')
        if isinstance(data, list) and data:
            item = data[0]
            if isinstance(item, dict):
                print(f'Keys: {list(item.keys())[:10]}')
                if 'cover' in item:
                    print(f'  cover: {item["cover"][:100]}')
                if 'vertical_cover' in item:
                    print(f'  vertical_cover: {item["vertical_cover"][:100]}')
