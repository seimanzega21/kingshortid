#!/usr/bin/env python3
"""Extract key API info for building the auto-scraper"""
import json, sys, io
from urllib.parse import urlparse, parse_qs
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open('melolo1.har', 'r', encoding='utf-8') as f:
    har = json.load(f)

output = {}

# 1. Extract headers + POST body from video_model
for entry in har['log']['entries']:
    url = entry['request']['url']
    if 'multi_video_model' not in url:
        continue
    req = entry['request']
    
    # Headers
    headers = {}
    for h in req['headers']:
        name = h['name'].lower()
        val = h['value']
        headers[name] = val
    
    # Query params
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    flat_params = {k: v[0] for k, v in params.items()}
    
    # POST body
    post_body = req.get('postData', {}).get('text', '')
    
    output['video_model'] = {
        'method': req['method'],
        'base_url': url.split('?')[0],
        'headers': headers,
        'params': flat_params,
        'post_body': post_body[:2000],
    }
    break

# 2. Same for video_detail
for entry in har['log']['entries']:
    url = entry['request']['url']
    if 'multi_video_detail' not in url:
        continue
    if 'video_model' in url:
        continue
    req = entry['request']
    
    headers = {}
    for h in req['headers']:
        headers[h['name'].lower()] = h['value']
    
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    flat_params = {k: v[0] for k, v in params.items()}
    
    post_body = req.get('postData', {}).get('text', '')
    
    output['video_detail'] = {
        'method': req['method'],
        'base_url': url.split('?')[0],
        'headers': headers,
        'params': flat_params,
        'post_body': post_body[:2000],
    }
    break

# 3. All series with their full vid lists
series_data = {}
for entry in har['log']['entries']:
    url = entry['request']['url']
    if 'video_detail' not in url or 'video_model' in url:
        continue
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
    if not isinstance(data.get('data'), dict):
        continue
    
    for k, v in data['data'].items():
        if not isinstance(v, dict):
            continue
        vd = v.get('video_data', {})
        if not isinstance(vd, dict):
            continue
        vl = vd.get('video_list', [])
        if not vl:
            continue
        
        book_name = vd.get('book_name', '')
        total_ep = vd.get('total_episode', len(vl))
        cover_url = vd.get('cover_url', '')
        abstract = vd.get('abstract', '')
        book_id = vd.get('book_id', '')
        
        key = book_name or k
        if key not in series_data or len(vl) > len(series_data[key].get('vids', [])):
            all_vids = []
            for item in vl:
                if isinstance(item, dict):
                    vid = item.get('vid', '')
                    idx = item.get('vid_index', 0)
                    if vid:
                        all_vids.append({'vid': vid, 'index': idx})
            
            series_data[key] = {
                'series_id': k,
                'book_id': str(book_id),
                'book_name': book_name,
                'total_episodes': total_ep,
                'cover_url': cover_url,
                'abstract': abstract[:200],
                'vids': all_vids,
            }

output['series'] = series_data

# Save
with open('api_replay_data.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

# Print summary
print(f"Saved api_replay_data.json")
print(f"\nVideo Model: {output['video_model']['method']} {output['video_model']['base_url']}")
print(f"  Key headers: {', '.join(k for k in output['video_model']['headers'] if k.startswith('x-') or k in ['cookie','authorization'])}")
print(f"  Has post body: {'Yes' if output['video_model']['post_body'] else 'No'}")

print(f"\nVideo Detail: {output['video_detail']['method']} {output['video_detail']['base_url']}")
print(f"  Key headers: {', '.join(k for k in output['video_detail']['headers'] if k.startswith('x-') or k in ['cookie','authorization'])}")

print(f"\nSeries found: {len(series_data)}")
total_vids = sum(len(s['vids']) for s in series_data.values())
print(f"Total episode vids available: {total_vids}")
for name, info in sorted(series_data.items(), key=lambda x: -x[1]['total_episodes']):
    t = info['book_name'] or f"(series {info['series_id'][-8:]})"
    print(f"  {t[:48]:<50} Total: {info['total_episodes']:>3}  VIDs: {len(info['vids'])}")
