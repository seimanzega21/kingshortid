#!/usr/bin/env python3
"""
Batch fix covers for all MP4 dramas that are missing covers on R2.
Uses the Melolo video_detail API to find covers, converts HEIC→JPEG via ffmpeg.
"""
import json, os, sys, time, requests, boto3, subprocess
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

# Extract API template from HAR
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
                    'headers': headers,
                    'params': params,
                    'body': body
                }
    return None

def find_images_in_response(obj, depth=0):
    """Deep search for image URLs in API response"""
    results = []
    if depth > 8: return results
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str) and 'http' in v and any(ext in v.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp', 'image']):
                is_cover = any(kw in k.lower() for kw in ['cover', 'poster', 'horizontal'])
                results.append((v, is_cover))
            results.extend(find_images_in_response(v, depth+1))
    elif isinstance(obj, list):
        for item in obj:
            results.extend(find_images_in_response(item, depth+1))
    return results

def download_and_convert_cover(url, slug):
    """Download cover, convert HEIC→JPEG if needed, return local path"""
    local_dir = base / slug
    local_dir.mkdir(parents=True, exist_ok=True)
    
    tmp_path = local_dir / 'cover_raw'
    try:
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        tmp_path.write_bytes(r.content)
    except Exception as e:
        print(f"    Download failed: {e}")
        return None
    
    data = tmp_path.read_bytes()
    
    # Check if JPEG already
    if data[:3] == bytes([0xFF, 0xD8, 0xFF]):
        final = local_dir / 'cover.jpg'
        final.write_bytes(data)
        tmp_path.unlink()
        return final
    
    # Convert with ffmpeg (handles HEIC, WEBP, etc.)
    final = local_dir / 'cover.jpg'
    try:
        subprocess.run(
            ['ffmpeg', '-i', str(tmp_path), '-y', str(final)],
            capture_output=True, timeout=30
        )
        tmp_path.unlink(missing_ok=True)
        
        # Verify it's JPEG now
        converted = final.read_bytes()
        if converted[:3] == bytes([0xFF, 0xD8, 0xFF]):
            return final
        else:
            print(f"    ffmpeg output not JPEG")
            return None
    except Exception as e:
        print(f"    ffmpeg failed: {e}")
        tmp_path.unlink(missing_ok=True)
        return None

def check_cover_on_r2(slug):
    """Check if a valid JPEG cover exists on R2"""
    for name in ['poster.jpg', 'cover.jpg', 'cover.png', 'cover.webp']:
        try:
            r = requests.head(f"{R2_PUBLIC}/melolo/{slug}/{name}", timeout=5)
            if r.status_code == 200:
                # Quick format check
                data = requests.get(f"{R2_PUBLIC}/melolo/{slug}/{name}", timeout=10).content
                if data[:3] == bytes([0xFF, 0xD8, 0xFF]) or data[:4] == bytes([0x89, 0x50, 0x4E, 0x47]):
                    return name  # Valid image exists
        except:
            pass
    return None

def main():
    print("=" * 60)
    print("  BATCH FIX COVERS FOR MP4 DRAMAS")
    print("=" * 60)
    
    template = get_api_template()
    if not template:
        print("ERROR: No API template found in HAR files!")
        sys.exit(1)
    print("API template loaded ✅\n")
    
    # Find MP4 dramas missing covers
    missing = []
    for d in sorted(base.iterdir()):
        if not d.is_dir():
            continue
        meta_path = d / 'metadata.json'
        if not meta_path.exists():
            continue
        meta = json.load(open(meta_path, 'r', encoding='utf-8'))
        if meta.get('format') != 'mp4':
            continue
        
        # Check R2
        existing = check_cover_on_r2(d.name)
        if existing:
            print(f"  ⏭ {d.name}: already has {existing}")
        else:
            missing.append((d.name, meta))
    
    print(f"\n  Missing covers: {len(missing)}")
    
    fixed = 0
    failed = 0
    
    for slug, meta in missing:
        series_id = meta.get('series_id', '')
        print(f"\n  [{fixed+failed+1}/{len(missing)}] {meta['title']} (series: {series_id})")
        
        # Call API
        body = dict(template['body'])
        body['series_id'] = series_id
        params = dict(template['params'])
        params['_rticket'] = str(int(time.time() * 1000))
        
        try:
            r = requests.post(template['base_url'], params=params, 
                            headers=template['headers'], json=body, timeout=20)
            if r.status_code != 200:
                print(f"    API error: {r.status_code}")
                failed += 1
                time.sleep(2)
                continue
            
            data = r.json()
            images = find_images_in_response(data)
            
            # Prefer cover/poster URLs
            cover_url = None
            for url, is_cover in images:
                if is_cover:
                    cover_url = url
                    break
            if not cover_url and images:
                cover_url = images[0][0]
            
            if not cover_url:
                print(f"    No image URL found in API response")
                failed += 1
                continue
            
            print(f"    Cover URL: {cover_url[:80]}")
            
            # Download and convert
            local_path = download_and_convert_cover(cover_url, slug)
            if not local_path:
                failed += 1
                continue
            
            # Upload to R2 as poster.jpg (bypass CDN cache on cover.jpg)
            r2_key = f'melolo/{slug}/poster.jpg'
            s3.upload_file(str(local_path), R2_BUCKET, r2_key,
                          ExtraArgs={'ContentType': 'image/jpeg'})
            print(f"    ✅ Uploaded: {r2_key} ({local_path.stat().st_size} bytes)")
            fixed += 1
            
            time.sleep(1)  # Rate limit
            
        except Exception as e:
            print(f"    Error: {e}")
            failed += 1
            time.sleep(2)
    
    print(f"\n{'=' * 60}")
    print(f"  DONE: {fixed} fixed, {failed} failed")
    print(f"{'=' * 60}")

if __name__ == '__main__':
    main()
