#!/usr/bin/env python3
"""Find the CORRECT drama poster cover from all HAR sources"""
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open('melolo1.har', 'r', encoding='utf-8') as f:
    har = json.load(f)

results = []

# Check EVERY JSON response for cover/poster/thumb fields
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

    endpoint = url.split('?')[0].split('tmtreader.com')[-1] if 'tmtreader.com' in url else url.split('?')[0][-60:]

    def scan(obj, path="root", depth=0):
        if depth > 6:
            return
        if isinstance(obj, dict):
            for k, v in obj.items():
                kl = k.lower()
                if isinstance(v, str) and v.startswith('http'):
                    if any(x in kl for x in ['cover', 'poster', 'thumb', 'image', 'pic', 'banner', 'icon']):
                        results.append({
                            'endpoint': endpoint,
                            'field': path + "." + k,
                            'url': v,
                        })
                elif isinstance(v, (dict, list)):
                    scan(v, path + "." + k, depth + 1)
        elif isinstance(obj, list) and len(obj) > 0:
            scan(obj[0], path + "[0]", depth + 1)

    scan(data)

# Deduplicate by field name and show
print(f"Total cover-like fields found: {len(results)}")

# Group by endpoint
by_endpoint = {}
for r in results:
    ep = r['endpoint']
    if ep not in by_endpoint:
        by_endpoint[ep] = []
    by_endpoint[ep].append(r)

for ep, items in sorted(by_endpoint.items()):
    print(f"\n=== {ep} ===")
    seen_fields = set()
    for item in items:
        field = item['field']
        if field not in seen_fields:
            seen_fields.add(field)
            print(f"  {field}")
            print(f"    {item['url'][:130]}")
