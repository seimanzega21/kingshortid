#!/usr/bin/env python3
"""Fix covers for specific dramas — any format (HLS or MP4)"""
import json, os, sys, time, subprocess, tempfile, requests, boto3
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / '.env')

R2_ENDPOINT = os.getenv('R2_ENDPOINT')
R2_ACCESS_KEY_ID = os.getenv('R2_ACCESS_KEY_ID')
R2_SECRET_ACCESS_KEY = os.getenv('R2_SECRET_ACCESS_KEY')
R2_BUCKET = os.getenv('R2_BUCKET_NAME', 'shortlovers')
R2_PUBLIC = 'https://stream.shortlovers.id'

s3 = boto3.client('s3', endpoint_url=R2_ENDPOINT,
                   aws_access_key_id=R2_ACCESS_KEY_ID,
                   aws_secret_access_key=R2_SECRET_ACCESS_KEY,
                   region_name='auto')

base = Path('r2_ready/melolo')

# Dramas to fix
TARGET_TITLES = [
    "Misi Cinta Sang Kurir",
    "Mata Sakti Mengungkap Rahasia",
    "Mata Ajaib di Pasar Barang Antik",
    "Mata Kiri Ajaibku",
    "Lelaki Bermata Dewa",
]

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

def find_images(obj, depth=0):
    results = []
    if depth > 8: return results
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str) and 'http' in v and any(ext in v.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp', 'image']):
                is_cover = any(kw in k.lower() for kw in ['cover', 'poster', 'horizontal'])
                results.append((v, is_cover))
            results.extend(find_images(v, depth+1))
    elif isinstance(obj, list):
        for item in obj:
            results.extend(find_images(item, depth+1))
    return results

def download_convert_upload(cover_url, slug):
    """Download cover, convert HEIC→JPEG if needed, upload to R2"""
    try:
        r = requests.get(cover_url, timeout=30)
        r.raise_for_status()
        data = r.content
        
        # Check if HEIC
        if data[:4] in (bytes([0x00,0x00,0x00,0x1C]), bytes([0x00,0x00,0x00,0x18])):
            # Convert via ffmpeg
            with tempfile.NamedTemporaryFile(suffix='.heic', delete=False) as tmp:
                tmp.write(data)
                tmp_in = tmp.name
            tmp_out = tmp_in.replace('.heic', '.jpg')
            try:
                subprocess.run(['ffmpeg', '-i', tmp_in, '-y', tmp_out],
                              capture_output=True, timeout=30)
                data = open(tmp_out, 'rb').read()
            finally:
                for p in (tmp_in, tmp_out):
                    try: os.unlink(p)
                    except: pass
        
        if data[:3] != bytes([0xFF,0xD8,0xFF]) and data[:4] != bytes([0x89,0x50,0x4E,0x47]):
            print(f"    ❌ Not a valid image after conversion")
            return False
        
        r2_key = f'melolo/{slug}/poster.jpg'
        s3.put_object(Bucket=R2_BUCKET, Key=r2_key, Body=data, ContentType='image/jpeg')
        print(f"    ✅ Uploaded: {r2_key} ({len(data)} bytes)")
        return True
    except Exception as e:
        print(f"    ❌ Error: {e}")
        return False

def main():
    print("=" * 60)
    print("  FIX COVERS FOR SPECIFIC DRAMAS")
    print("=" * 60)
    
    template = get_api_template()
    if not template:
        print("ERROR: No API template!")
        sys.exit(1)
    
    # Find slugs by title
    target_lower = [t.lower() for t in TARGET_TITLES]
    dramas = []
    
    for d in sorted(base.iterdir()):
        if not d.is_dir():
            continue
        meta_path = d / 'metadata.json'
        if not meta_path.exists():
            continue
        meta = json.load(open(meta_path, 'r', encoding='utf-8'))
        if meta.get('title', '').lower() in target_lower:
            dramas.append((d.name, meta))
    
    print(f"\n  Found {len(dramas)}/{len(TARGET_TITLES)} target dramas\n")
    
    # Also check if they're already OK
    fixed = 0
    for slug, meta in dramas:
        title = meta['title']
        series_id = meta.get('series_id', '')
        print(f"  [{fixed+1}] {title} ({slug})")
        
        # Check if valid cover already exists on R2
        for name in ['poster.jpg', 'cover.jpg']:
            try:
                r = requests.get(f"{R2_PUBLIC}/melolo/{slug}/{name}", timeout=5)
                if r.status_code == 200 and r.content[:3] == bytes([0xFF,0xD8,0xFF]):
                    print(f"    Already has valid {name} — skipping")
                    # But make sure DB points to it
                    continue
            except:
                pass
        
        # Fetch from API
        body = dict(template['body'])
        body['series_id'] = series_id
        params = dict(template['params'])
        params['_rticket'] = str(int(time.time() * 1000))
        
        try:
            r = requests.post(template['base_url'], params=params,
                            headers=template['headers'], json=body, timeout=20)
            if r.status_code != 200:
                print(f"    API error: {r.status_code}")
                continue
            
            data = r.json()
            images = find_images(data)
            
            cover_url = None
            for url, is_cover in images:
                if is_cover:
                    cover_url = url
                    break
            if not cover_url and images:
                cover_url = images[0][0]
            
            if not cover_url:
                print(f"    No cover URL from API")
                continue
            
            print(f"    Cover: {cover_url[:80]}")
            if download_convert_upload(cover_url, slug):
                fixed += 1
            
            time.sleep(1)
        except Exception as e:
            print(f"    Error: {e}")
    
    # Update DB cover URLs
    print(f"\n  Now updating DB cover URLs...")
    # We'll print the slugs so import script can pick them up
    for slug, meta in dramas:
        print(f"    {slug} -> poster.jpg")
    
    print(f"\n{'=' * 60}")
    print(f"  DONE: {fixed} covers fixed")
    print(f"{'=' * 60}")

if __name__ == '__main__':
    main()
