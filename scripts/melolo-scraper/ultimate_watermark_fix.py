import os
import re
import time
import requests
import urllib3
urllib3.disable_warnings()

from difflib import SequenceMatcher
import boto3
from dotenv import load_dotenv

load_dotenv(r'd:\kingshortid\scripts\melolo-scraper\.env')
s3 = boto3.client('s3', 
    endpoint_url=os.getenv('R2_ENDPOINT'), 
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'), 
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'), 
    region_name='auto'
)

def similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def get_netshort_mappings():
    data = open(r'd:\kingshortid\scripts\melolo-scraper\netshort_scrape.log', encoding='utf-8', errors='ignore').read()
    matches = re.findall(r'Scraping drama:\s*(\d+).*?\n.*?Title:\s*([^\n]+)', data, re.IGNORECASE)
    return {title.strip(): did for did, title in set(matches)}

def fetch_netshort_cover(did):
    r = requests.get(f'https://vidrama.asia/api/netshort/api/drama/{did}?lang=in', headers={'User-Agent':'Mozilla/5.0'}, verify=False, timeout=10)
    if r.status_code == 200:
        return r.json().get('shortPlayCover')
    return None

def main():
    headers = {'Authorization': 'Bearer 00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'}
    log_mappings = get_netshort_mappings()
    
    print(f"Found {len(log_mappings)} mapped dramas in log.")
    
    r = requests.get('http://localhost:3000/api/dramas?limit=1000&includeInactive=true', headers=headers).json()
    local_dramas = [d for d in r.get('dramas', []) if d.get('cover') and 'netshort' in d['cover'].lower()]
    
    print(f"Checking {len(local_dramas)} Netshort dramas in local DB...")
    
    fixed_count = 0
    t = int(time.time())
    
    for d in local_dramas:
        local_title = d.get('title', '')
        
        # 1. Find matching ID
        best_match_title = None
        best_match_score = 0
        for log_title in log_mappings.keys():
            clean_log = log_title.replace('(Sulih suara)', '').strip()
            score = similar(local_title, clean_log)
            if score > best_match_score:
                best_match_score = score
                best_match_title = log_title
                
        if best_match_score < 0.8:
            print(f"⚠️ No exact match found for: {local_title} (best was {best_match_title} at {best_match_score})")
            continue
            
        did = log_mappings[best_match_title]
        
        # 2. Extract S3 Path from existing DB URL
        orig_cover_url = d['cover'].split('?')[0] # e.g. https://.../dramas/netshort/.../cover.jpg
        s3_key = orig_cover_url.split('.id/')[-1] # gets dramas/netshort/.../cover.jpg
        slug_dir = '/'.join(s3_key.split('/')[:-1]) # dramas/netshort/...
        
        # 3. Download Source Image
        source_url = fetch_netshort_cover(did)
        if not source_url:
            print(f"❌ Failed to get API cover for ID {did} ({local_title})")
            continue
            
        img_res = requests.get(source_url, verify=False, timeout=10)
        if img_res.status_code != 200:
            print(f"❌ Failed to download source image for {local_title}")
            continue
            
        img_data = img_res.content
        ctype = img_res.headers.get('content-type', 'image/jpeg')
        
        # 4. Upload to R2 cleanly!
        try:
            s3.put_object(Bucket='shortlovers', Key=f"{slug_dir}/cover.jpg", Body=img_data, ContentType=ctype, CacheControl='no-cache, max-age=0')
            s3.put_object(Bucket='shortlovers', Key=f"{slug_dir}/cover.webp", Body=img_data, ContentType=ctype, CacheControl='no-cache, max-age=0')
            s3.put_object(Bucket='shortlovers', Key=f"{slug_dir}/poster.webp", Body=img_data, ContentType=ctype, CacheControl='no-cache, max-age=0')
        except Exception as e:
            print(f"❌ Error uploading {local_title} to R2: {e}")
            continue
            
        # 5. Cache-bust Database!
        nc = orig_cover_url + f"?v={t}"
        patch_res = requests.patch(f"http://localhost:3000/api/dramas/{d['id']}", json={'cover': nc, 'coverUrl': nc}, headers=headers)
        
        if patch_res.status_code == 200:
            print(f"✅ Fixed & Busted: {local_title}")
            fixed_count += 1
        else:
            print(f"⚠️ Uploaded but failed to patch DB for: {local_title}")
            
    print(f"\nFINISH! Entirely restored and cache-busted {fixed_count} covers.")

if __name__ == "__main__":
    main()
