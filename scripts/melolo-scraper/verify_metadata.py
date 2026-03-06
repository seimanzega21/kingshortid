#!/usr/bin/env python3
"""Verify & fix ALL dramas that had empty metadata — fetch correct series_name from API"""
import json, os, sys, time, requests
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / '.env')

base = Path('r2_ready/melolo')

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

def fetch_series_info(template, series_id):
    """Fetch series info and return ALL relevant fields for manual inspection"""
    body = dict(template['body'])
    body['series_id'] = series_id
    params = dict(template['params'])
    params['_rticket'] = str(int(time.time() * 1000))
    
    r = requests.post(template['base_url'], params=params,
                      headers=template['headers'], json=body, timeout=20)
    if r.status_code != 200:
        return None
    
    data = r.json()
    
    # Collect ALL name/title/intro fields from the entire response
    fields = {}
    def collect(obj, path='', depth=0):
        if depth > 10: return
        if isinstance(obj, dict):
            for k, v in obj.items():
                full = f"{path}.{k}" if path else k
                if isinstance(v, str) and v.strip():
                    # Only collect name/title/intro/description fields
                    if any(kw in k.lower() for kw in ['name', 'title', 'intro', 'description', 'series_name']):
                        fields[full] = v
                elif isinstance(v, (dict, list)):
                    collect(v, full, depth+1)
        elif isinstance(obj, list):
            for i, item in enumerate(obj[:2]):  # only first 2 items
                collect(item, f"{path}[{i}]", depth+1)
    
    collect(data)
    return fields

def main():
    print("=" * 70)
    print("  VERIFY ALL DRAMA METADATA — Compare local vs API")
    print("=" * 70)
    
    template = get_api_template()
    if not template:
        print("ERROR: No API template!")
        sys.exit(1)
    print("API template loaded ✅\n")
    
    # Check ALL dramas, not just bad ones
    results = []
    for d in sorted(base.iterdir()):
        if not d.is_dir(): continue
        meta_path = d / 'metadata.json'
        if not meta_path.exists(): continue
        meta = json.load(open(meta_path, 'r', encoding='utf-8'))
        results.append((d.name, meta, meta_path))
    
    issues = []
    for slug, meta, meta_path in results:
        series_id = meta.get('series_id', '')
        local_title = meta.get('title', '').strip()
        local_desc = meta.get('description', '').strip()
        
        if not series_id: continue
        
        print(f"\n  {slug}")
        print(f"    Local title: \"{local_title}\"")
        
        # Fetch from API
        try:
            fields = fetch_series_info(template, series_id)
            if not fields:
                print(f"    ❌ API failed")
                continue
            
            # Find the REAL series_name (top-level, not nested in video items)
            api_title = ''
            api_desc = ''
            
            for path, val in sorted(fields.items()):
                # series_name at data.video_data level = real title
                if 'series_name' in path and 'video_list' not in path:
                    if val.strip():
                        api_title = val.strip()
                if 'series_intro' in path and 'video_list' not in path:
                    if val.strip():
                        api_desc = val.strip()
            
            # If no series_name found, show all available name fields
            if not api_title:
                print(f"    API series_name: (empty)")
                name_fields = {k: v for k, v in fields.items() if 'name' in k.lower() or 'title' in k.lower()}
                for k, v in name_fields.items():
                    print(f"      {k}: \"{v[:80]}\"")
            else:
                print(f"    API series_name: \"{api_title}\"")
            
            if api_desc:
                print(f"    API series_intro: \"{api_desc[:80]}...\"")
            
            # Check for mismatches
            if api_title and local_title and api_title != local_title:
                print(f"    ⚠️  MISMATCH: local=\"{local_title}\" vs api=\"{api_title}\"")
                issues.append((slug, meta_path, local_title, api_title, api_desc))
            elif api_title and not local_title:
                print(f"    ⚠️  LOCAL EMPTY — should be \"{api_title}\"")
                issues.append((slug, meta_path, local_title, api_title, api_desc))
            elif local_title:
                print(f"    ✅ Match")
            
            time.sleep(0.5)
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    print(f"\n{'=' * 70}")
    print(f"  SUMMARY: {len(issues)} dramas with title mismatches")
    print(f"{'=' * 70}")
    
    for slug, meta_path, local, api, desc in issues:
        print(f"\n  {slug}:")
        print(f"    Current: \"{local}\"")
        print(f"    Should be: \"{api}\"")
    
    # Auto-fix mismatches
    if issues:
        print(f"\n  Fixing {len(issues)} mismatches...")
        for slug, meta_path, local, api_title, api_desc in issues:
            meta = json.load(open(meta_path, 'r', encoding='utf-8'))
            if api_title:
                meta['title'] = api_title
            if api_desc and (not meta.get('description') or len(meta['description']) < 10):
                meta['description'] = api_desc
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
            print(f"    ✅ {slug}: \"{api_title}\"")
    
    print(f"\n  Done!")

if __name__ == '__main__':
    main()
