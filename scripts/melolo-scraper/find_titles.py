#!/usr/bin/env python3
"""
Build final title mapping: book_id -> title+abstract from ALL endpoints.
Then check coverage against our 72 drama series.
"""
import json, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open('melolo1.har', 'r', encoding='utf-8') as f:
    har = json.load(f)

# 1. Collect ALL book metadata from EVERY endpoint
book_data = {}  # book_id -> {title, abstract, categories, ...}

for entry in har['log']['entries']:
    url = entry['request']['url']
    mime = entry['response']['content'].get('mimeType', '')
    if 'json' not in mime:
        continue
    text = entry['response']['content'].get('text', '')
    if not text:
        continue
    try:
        data = json.loads(text)
    except:
        continue

    endpoint = url.split('?')[0].split('tmtreader.com')[-1] if 'tmtreader.com' in url else ''

    def extract(obj, depth=0):
        if depth > 6 or not isinstance(obj, (dict, list)):
            return
        if isinstance(obj, dict):
            bid = str(obj.get('book_id', ''))
            bname = obj.get('book_name', '')
            abstract = obj.get('abstract', '')
            
            if bid and bname and len(bid) > 10:  # Looks like a real book_id
                if bid not in book_data or len(abstract) > len(book_data[bid].get('abstract', '')):
                    # Parse categories
                    cats = []
                    cat_info = obj.get('category_info', '')
                    if isinstance(cat_info, str) and cat_info:
                        try:
                            cl = json.loads(cat_info)
                            cats = [c['Name'] for c in cl if isinstance(c, dict) and c.get('Name')]
                        except:
                            pass
                    elif isinstance(cat_info, list):
                        cats = [c['Name'] for c in cat_info if isinstance(c, dict) and c.get('Name')]
                    
                    book_data[bid] = {
                        'title': bname,
                        'abstract': abstract,
                        'categories': cats,
                        'serial_count': obj.get('serial_count', 0),
                        'author': obj.get('author', ''),
                        'source': endpoint,
                    }
            
            for v in obj.values():
                extract(v, depth + 1)
        elif isinstance(obj, list):
            for item in obj[:50]:
                extract(item, depth + 1)
    
    extract(data)

print(f"Total book metadata collected: {len(book_data)}")

# 2. Get all our series IDs from video_detail
series_ids = set()
series_descriptions = {}  # series_id -> description from video_data.book_name

for entry in har['log']['entries']:
    url = entry['request']['url']
    if 'video_detail' not in url or 'video_model' in url:
        continue
    text = entry['response']['content'].get('text', '')
    if not text:
        continue
    try:
        data = json.loads(text)
    except:
        continue
    if not isinstance(data.get('data'), dict):
        continue
    
    for k, v in data['data'].items():
        if not isinstance(v, dict):
            continue
        vd = v.get('video_data')
        if not isinstance(vd, dict):
            continue
        vl = vd.get('video_list', [])
        if vl:
            series_ids.add(k)
            bn = vd.get('book_name', '')
            if bn:
                series_descriptions[k] = bn

print(f"Series IDs from video_detail: {len(series_ids)}")

# 3. Match series_ids to book_data
matched = {}
unmatched = []

for sid in sorted(series_ids):
    if sid in book_data:
        matched[sid] = book_data[sid]
    else:
        unmatched.append(sid)

print(f"\nDirect book_id match: {len(matched)}/{len(series_ids)}")
print(f"Unmatched: {len(unmatched)}")

# 4. For unmatched, try to use video_data.book_name as description (it's actually a synopsis, not title)
# and cross-reference via series_cover hash
series_covers = {}
for entry in har['log']['entries']:
    url = entry['request']['url']
    if 'video_detail' not in url or 'video_model' in url:
        continue
    text = entry['response']['content'].get('text', '')
    if not text:
        continue
    try:
        data = json.loads(text)
    except:
        continue
    if not isinstance(data.get('data'), dict):
        continue
    for k, v in data['data'].items():
        if not isinstance(v, dict):
            continue
        vd = v.get('video_data')
        if not isinstance(vd, dict):
            continue
        sc = vd.get('series_cover', '')
        if sc:
            m = re.search(r'/([a-f0-9]{32})', sc)
            if m:
                series_covers[k] = m.group(1)

# Get thumb_url -> title mapping
thumb_titles = {}
for bid, info in book_data.items():
    # We need to get thumb_url for this book
    pass

# Actually let's scan again specifically for thumb_url -> book_name
hash_to_title = {}
for entry in har['log']['entries']:
    text = entry['response']['content'].get('text', '')
    if not text:
        continue
    mime = entry['response']['content'].get('mimeType', '')
    if 'json' not in mime:
        continue
    try:
        data = json.loads(text)
    except:
        continue
    
    def scan_thumbs(obj, depth=0):
        if depth > 6 or not isinstance(obj, (dict, list)):
            return
        if isinstance(obj, dict):
            bname = obj.get('book_name', '')
            thumb = obj.get('thumb_url', '')
            abstract = obj.get('abstract', '')
            if bname and thumb:
                m = re.search(r'/([a-f0-9]{32})', thumb)
                if m:
                    hash_to_title[m.group(1)] = {'title': bname, 'abstract': abstract}
            for v in obj.values():
                scan_thumbs(v, depth + 1)
        elif isinstance(obj, list):
            for item in obj[:50]:
                scan_thumbs(item, depth + 1)
    
    scan_thumbs(data)

# Try to match unmatched via cover hash
hash_matched = 0
for sid in unmatched[:]:
    if sid in series_covers:
        h = series_covers[sid]
        if h in hash_to_title:
            info = hash_to_title[h]
            matched[sid] = {
                'title': info['title'],
                'abstract': info['abstract'],
                'categories': [],
                'source': 'cover_hash_match',
            }
            unmatched.remove(sid)
            hash_matched += 1

print(f"Hash matched additional: {hash_matched}")
print(f"Final matched: {len(matched)}/{len(series_ids)}")
print(f"Still unmatched: {len(unmatched)}")

if unmatched:
    print("\nUnmatched series (will use synopsis as description, no title):")
    for sid in unmatched:
        desc = series_descriptions.get(sid, '(no data)')[:60]
        print(f"  {sid}: {desc}")

# 5. Save final mapping
final_mapping = {}
for sid in series_ids:
    if sid in matched:
        m = matched[sid]
        final_mapping[sid] = {
            'title': m['title'],
            'abstract': m['abstract'],
            'categories': m.get('categories', []),
            'author': m.get('author', ''),
        }
    else:
        # Use synopsis from video_data as description, no title
        final_mapping[sid] = {
            'title': '',
            'abstract': series_descriptions.get(sid, ''),
            'categories': [],
            'author': '',
        }

with open('final_title_mapping.json', 'w', encoding='utf-8') as f:
    json.dump(final_mapping, f, indent=2, ensure_ascii=False)

print(f"\nSaved final_title_mapping.json ({len(final_mapping)} entries)")
print(f"\nSummary:")
with_title = sum(1 for v in final_mapping.values() if v['title'])
with_abstract = sum(1 for v in final_mapping.values() if v['abstract'])
print(f"  With title: {with_title}/{len(final_mapping)}")
print(f"  With abstract: {with_abstract}/{len(final_mapping)}")

# Show all matched titles
print(f"\n\n=== ALL MATCHED TITLES ===\n")
for sid in sorted(matched, key=lambda x: matched[x]['title']):
    info = matched[sid]
    print(f"  {sid[-12:]}: {info['title']}")
