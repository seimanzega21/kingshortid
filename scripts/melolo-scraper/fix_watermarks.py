import os
import re
import io
import time
import requests
import boto3
from pathlib import Path
from dotenv import load_dotenv

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")

def main():
    print("="*60)
    print("FIXING KSHORT WATERMARKS IN R2 COVERS")
    print("="*60)
    
    # 1. Setup AWS S3 / R2 client
    load_dotenv('d:\\kingshortid\\scripts\\melolo-scraper\\.env')
    R2_ENDPOINT = os.getenv('R2_ENDPOINT')
    R2_ACCESS_KEY = os.getenv('R2_ACCESS_KEY_ID')
    R2_SECRET_KEY = os.getenv('R2_SECRET_ACCESS_KEY')
    R2_BUCKET = os.getenv('R2_BUCKET_NAME', 'shortlovers')
    
    s3 = boto3.client('s3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        region_name='auto'
    )
    
    # 2. Parse ID mapping from log
    log_path = Path("d:/kingshortid/scripts/melolo-scraper/netshort_scrape.log")
    log_data = log_path.read_text(encoding="utf-8", errors="ignore")
    
    matches = re.findall(r"Scraping drama:\s*(\d+).*?\n.*?Title:\s*([^\n]+)", log_data, re.IGNORECASE)
    
    slug_to_id = {}
    for did, title in matches:
        title = title.strip()
        slug = slugify(title)
        slug_to_id[slug] = did
        # Also map versions without "(Sulih suara)"
        clean_title = title.replace("(Sulih suara)", "").replace("(sulih suara)", "").strip()
        slug_to_id[slugify(clean_title)] = did
    
    print(f"Found {len(slug_to_id)} drama mappings in log.")
    
    # 3. List all netshort dramas in R2
    print("Scanning R2 netshort dramas...")
    r2_slugs = set()
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=R2_BUCKET, Prefix='dramas/netshort/', Delimiter='/'):
        for cp in page.get('CommonPrefixes', []):
            slug = cp['Prefix'].replace('dramas/netshort/', '').rstrip('/')
            r2_slugs.add(slug)
            
    print(f"Found {len(r2_slugs)} dramas on R2.")
    
    fixed_count = 0
    fail_count = 0
    
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    for slug in r2_slugs:
        print(f"\nProcessing: {slug}")
        ns_id = slug_to_id.get(slug)
        
        if not ns_id:
            print("  ❌ Could not find netshort ID mapping for this slug.")
            fail_count += 1
            continue
            
        print(f"  ID: {ns_id}")
        
        # 4. Fetch clean cover from Vidrama API
        api_url = f"https://vidrama.asia/api/netshort/api/drama/{ns_id}?lang=in"
        try:
            r = requests.get(api_url, headers={"User-Agent": "Mozilla/5.0"}, verify=False, timeout=15)
            if r.status_code != 200:
                print(f"  ❌ API returned {r.status_code}")
                fail_count += 1
                continue
                
            data = r.json()
            cover_url = data.get('shortPlayCover') or data.get('coverUrl') or data.get('image')
            if not cover_url:
                print("  ❌ API did not return cover image URL.")
                fail_count += 1
                continue
                
            print(f"  Clean Cover URL: {cover_url}")
            
            # Download image
            img_r = requests.get(cover_url, headers={"User-Agent": "Mozilla/5.0"}, verify=False, timeout=15)
            if img_r.status_code != 200:
                print(f"  ❌ Could not download image (HTTP {img_r.status_code})")
                fail_count += 1
                continue
                
            img_data = img_r.content
            
            # 5. Upload to R2 (overwrite cover.jpg AND cover.webp)
            # Find ContentType
            ctype = img_r.headers.get("content-type", "image/jpeg")
            
            s3.put_object(
                Bucket=R2_BUCKET,
                Key=f"dramas/netshort/{slug}/cover.jpg",
                Body=img_data,
                ContentType=ctype,
                CacheControl="no-cache, max-age=0"
            )
            
            s3.put_object(
                Bucket=R2_BUCKET,
                Key=f"dramas/netshort/{slug}/cover.webp",
                Body=img_data,
                ContentType=ctype,
                CacheControl="no-cache, max-age=0"
            )
            
            # Also overwrite poster in case they use it
            try:
                s3.put_object(Bucket=R2_BUCKET, Key=f"dramas/netshort/{slug}/poster.webp", Body=img_data, ContentType=ctype, CacheControl="no-cache, max-age=0")
            except: pass
            
            print("  ✅ Uploaded clean cover to R2 successfully.")
            fixed_count += 1
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
            fail_count += 1
            
        time.sleep(0.5)
        
    print("\n" + "="*60)
    print(f"FINISHED! Fixed: {fixed_count} | Failed: {fail_count}")
    print("="*60)

if __name__ == "__main__":
    main()
