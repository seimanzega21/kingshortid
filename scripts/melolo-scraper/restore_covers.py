#!/usr/bin/env python3
"""
restore_covers.py - Re-download and re-upload all Netshort drama covers to R2
This removes any previously applied KingShort logo overlay from cover images.
"""
import requests, time, tempfile
from pathlib import Path
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
import os
from dotenv import load_dotenv
import boto3

load_dotenv('d:\\kingshortid\\scripts\\melolo-scraper\\.env')
R2_ENDPOINT = os.getenv('R2_ENDPOINT')
R2_ACCESS_KEY = os.getenv('R2_ACCESS_KEY_ID')
R2_SECRET_KEY = os.getenv('R2_SECRET_ACCESS_KEY')
R2_BUCKET = os.getenv('R2_BUCKET_NAME', 'shortlovers')
R2_PUBLIC = 'https://stream.shortlovers.id'

ADMIN_KEY = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
HEADERS_AUTH = {'Authorization': f'Bearer {ADMIN_KEY}'}
NETSHORT_HEADERS = {
    'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json',
    'Origin': 'https://vidrama.asia', 'Referer': 'https://vidrama.asia/'
}

def get_s3():
    return boto3.client('s3', endpoint_url=R2_ENDPOINT,
                        aws_access_key_id=R2_ACCESS_KEY,
                        aws_secret_access_key=R2_SECRET_KEY, region_name='auto')

# 1. Fetch all Netshort dramas from local backend
print('Fetching all Netshort dramas...')
r = requests.get('http://localhost:3000/api/dramas', headers=HEADERS_AUTH,
                 params={'limit': 999, 'includeInactive': 'true'})
all_dramas = r.json().get('dramas', [])

# Filter only Netshort dramas (cover URL contains 'netshort')
netshort_dramas = [d for d in all_dramas if 'netshort' in d.get('cover', '')]
print(f'Found {len(netshort_dramas)} Netshort dramas with covers in R2')

# 2. Load state file to get Netshort drama IDs
import json
STATE_FILE = Path('d:/kingshortid/scripts/melolo-scraper/netshort_state.json')
state = {}
if STATE_FILE.exists():
    state = json.loads(STATE_FILE.read_text(encoding='utf-8'))

scraped_map = state.get('scraped', {})  # netshort_id -> {title, slug, ...}

# Build reverse map: slug -> netshort_id
slug_to_nsid = {}
for ns_id, info in scraped_map.items():
    slug = info.get('slug', '')
    if slug:
        slug_to_nsid[slug] = ns_id

print(f'State file has {len(scraped_map)} scraped dramas')

s3 = get_s3()
TEMP_DIR = Path(tempfile.gettempdir()) / 'restore_covers'
TEMP_DIR.mkdir(exist_ok=True)

ok, skip, fail = 0, 0, 0

for drama in netshort_dramas:
    title = drama.get('title', '')
    cover_url = drama.get('cover', '')
    backend_id = drama.get('id', '')
    
    # Extract slug from cover URL: https://stream.shortlovers.id/dramas/netshort/{slug}/cover.jpg
    if 'netshort/' not in cover_url:
        skip += 1
        continue
    
    slug = cover_url.split('netshort/')[1].split('/')[0]
    
    # Get Netshort drama ID from state file
    ns_id = slug_to_nsid.get(slug)
    
    if not ns_id:
        # Try to find via search
        search_title = title.replace('(Sulih suara)', '').replace('(sulih suara)', '').strip()
        r2 = requests.get('https://vidrama.asia/api/netshort/api/search',
                          headers=NETSHORT_HEADERS, params={'lang': 'in', 'q': search_title[:30], 'page': 1})
        dd = (r2.json().get('data') or {})
        for key in ['simpleSearchResult', 'searchOnCaseSearchResult', 'contentInfos']:
            items = dd.get(key, [])
            for it in items:
                if not isinstance(it, dict): continue
                name = (it.get('shortPlayName') or it.get('name') or '').lower()
                words = [w for w in search_title.lower().split() if len(w) > 2]
                if sum(1 for w in words if w in name) >= max(1, len(words) - 1):
                    ns_id = str(it.get('shortPlayId') or it.get('id') or '')
                    break
            if ns_id:
                break
    
    if not ns_id:
        print(f'  [SKIP] Cannot find Netshort ID for "{title[:40]}"')
        skip += 1
        continue
    
    # Re-fetch original cover from Netshort
    try:
        rd = requests.get(f'https://vidrama.asia/api/netshort/api/drama/{ns_id}',
                          headers=NETSHORT_HEADERS, params={'lang': 'in'}, verify=False)
        drama_data = rd.json()
        if not isinstance(drama_data, dict):
            raise ValueError(f'Bad response: {str(drama_data)[:50]}')
        
        orig_cover_url = drama_data.get('shortPlayCover', '')
        if not orig_cover_url:
            print(f'  [SKIP] No cover URL for "{title[:40]}"')
            skip += 1
            continue
        
        # Download original cover
        cover_path = TEMP_DIR / f'{slug}_cover.jpg'
        rc = requests.get(orig_cover_url, headers={'User-Agent': 'Mozilla/5.0'}, 
                          stream=True, verify=False, timeout=30)
        with open(cover_path, 'wb') as f:
            for chunk in rc.iter_content(8192):
                f.write(chunk)
        
        # Upload to R2 (overwrite existing)
        r2_key = f'dramas/netshort/{slug}/cover.jpg'
        s3.upload_file(str(cover_path), R2_BUCKET, r2_key,
                       ExtraArgs={'ContentType': 'image/jpeg',
                                  'CacheControl': 'no-cache, max-age=0'})
        cover_path.unlink(missing_ok=True)
        
        print(f'  [OK] [{ok+1}] Restored: {title[:45]}')
        ok += 1
        
    except Exception as e:
        print(f'  [FAIL] {title[:40]} - {e}')
        fail += 1
    
    time.sleep(0.3)

import shutil
shutil.rmtree(TEMP_DIR, ignore_errors=True)
print(f'\n[DONE] Restored: {ok} | Skipped: {skip} | Failed: {fail}')
print('All Netshort covers restored to original (no logo).')
