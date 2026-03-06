#!/usr/bin/env python3
"""Dump raw API response to file for inspection"""
import json, os, time, requests
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / '.env')

SERIES_ID = '7582055834209750069'

def get_api_template():
    for har_file in sorted(Path('.').glob('*.har')):
        with open(har_file, 'r', encoding='utf-8') as f:
            har = json.load(f)
        for entry in har['log']['entries']:
            url = entry['request']['url']
            if 'video_detail/v1/' in url and 'multi' not in url:
                req = entry['request']
                parsed = urlparse(url)
                headers = {h['name']: h['value'] for h in req['headers']}
                params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
                body = {}
                if 'postData' in req:
                    try: body = json.loads(req['postData'].get('text', '{}'))
                    except: pass
                return {
                    'base_url': parsed.scheme + '://' + parsed.netloc + parsed.path,
                    'headers': headers, 'params': params, 'body': body
                }
    return None

template = get_api_template()
body = dict(template['body'])
body['series_id'] = SERIES_ID
params = dict(template['params'])
params['_rticket'] = str(int(time.time() * 1000))

r = requests.post(template['base_url'], params=params, headers=template['headers'], json=body, timeout=20)
data = r.json()

# Save to file
with open('debug_response.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

# Print top-level structure
def show_structure(obj, prefix='', depth=0, max_depth=3):
    if depth > max_depth: return
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str):
                print(f"{prefix}{k}: \"{v[:100]}\"")
            elif isinstance(v, (int, float, bool)):
                print(f"{prefix}{k}: {v}")
            elif isinstance(v, list):
                print(f"{prefix}{k}: [{len(v)} items]")
                if len(v) > 0:
                    show_structure(v[0], prefix + '  ', depth+1, max_depth)
            elif isinstance(v, dict):
                print(f"{prefix}{k}: {{...}}")
                show_structure(v, prefix + '  ', depth+1, max_depth)

print("=== Response structure ===\n")
show_structure(data)
