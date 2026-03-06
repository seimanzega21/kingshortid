#!/usr/bin/env python3
"""
Repair script: Fix missing covers + re-upload metadata & covers to R2
Also downloads covers from HAR-saved thumb_urls where missing.
"""
import json, sys, io, os, time, requests, boto3
from pathlib import Path
from dotenv import load_dotenv

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stdout.reconfigure(line_buffering=True)

load_dotenv(Path(__file__).parent / '.env')

R2_ENDPOINT = os.getenv('R2_ENDPOINT')
R2_ACCESS_KEY_ID = os.getenv('R2_ACCESS_KEY_ID')
R2_SECRET_ACCESS_KEY = os.getenv('R2_SECRET_ACCESS_KEY')
R2_BUCKET = os.getenv('R2_BUCKET_NAME', 'shortlovers')
R2_PUBLIC_URL = os.getenv('R2_PUBLIC_URL', 'https://stream.shortlovers.id')

CONTENT_TYPES = {
    '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png',
    '.json': 'application/json', '.m3u8': 'application/vnd.apple.mpegurl',
    '.ts': 'video/mp2t', '.mp4': 'video/mp4', '.webp': 'image/webp',
}

MELOLO_DIR = Path(__file__).parent / 'r2_ready' / 'melolo'


def get_r2_client():
    if not all([R2_ENDPOINT, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY]):
        return None
    return boto3.client('s3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name='auto'
    )


def load_har_thumb_urls(har_dir: Path) -> dict:
    """Extract thumb_url mappings from HAR files' bookmall responses"""
    urls = {}  # slug -> thumb_url
    
    for har_file in sorted(har_dir.glob('melolo*.har')):
        print(f"  Scanning {har_file.name}...")
        try:
            with open(har_file, 'r', encoding='utf-8') as f:
                har = json.load(f)
        except:
            continue
            
        for entry in har['log']['entries']:
            url = entry['request']['url']
            if 'bookmall/cell/change' not in url and '/tab/' not in url:
                continue
            
            text = entry['response']['content'].get('text', '')
            if not text:
                continue
                
            try:
                data = json.loads(text)
            except:
                continue
            
            # Actual structure: data.cell.cell_data[].books[]
            cell = data.get('data', {}).get('cell', {})
            cell_data_list = cell.get('cell_data', [])
            
            for cell_data in cell_data_list:
                if not isinstance(cell_data, dict):
                    continue
                for book in cell_data.get('books', []):
                    if not isinstance(book, dict):
                        continue
                    thumb = book.get('thumb_url', '')
                    title = book.get('book_name', '')
                    book_id = str(book.get('book_id', ''))
                    if thumb and title:
                        slug = slugify(title)
                        urls[slug] = thumb
                        urls[book_id] = thumb
    
    return urls


def slugify(text: str) -> str:
    import re
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')


def download_cover(thumb_url: str, cover_path: Path) -> bool:
    """Download cover image from thumb URL"""
    try:
        # Try multiple URL formats
        urls_to_try = [thumb_url]
        
        if '~tplv' in thumb_url:
            base = thumb_url.split('~')[0]
            urls_to_try.insert(0, base + '~tplv-resize:570:810.jpg')
            urls_to_try.append(base)
        
        for url in urls_to_try:
            try:
                resp = requests.get(url, timeout=15)
                if resp.status_code == 200 and len(resp.content) > 1000:
                    with open(cover_path, 'wb') as f:
                        f.write(resp.content)
                    return True
            except:
                continue
    except Exception as e:
        print(f"    ⚠ Download failed: {e}")
    return False


def upload_file_to_r2(s3, local_path: Path, r2_key: str) -> bool:
    """Upload a single file to R2"""
    ct = CONTENT_TYPES.get(local_path.suffix.lower(), 'application/octet-stream')
    try:
        s3.upload_file(str(local_path), R2_BUCKET, r2_key, ExtraArgs={'ContentType': ct})
        return True
    except Exception as e:
        print(f"    ⚠ Upload failed {r2_key}: {e}")
        return False


def main():
    print("=" * 60)
    print("  MELOLO REPAIR: FIX COVERS + UPLOAD METADATA TO R2")
    print("=" * 60)
    
    # 1. Connect to R2
    s3 = get_r2_client()
    if not s3:
        print("❌ R2 credentials missing!")
        sys.exit(1)
    
    try:
        s3.head_bucket(Bucket=R2_BUCKET)
        print(f"\n✅ R2 connected: {R2_BUCKET}")
    except Exception as e:
        print(f"❌ R2 connection failed: {e}")
        sys.exit(1)
    
    # 2. Load thumb URLs from HAR files
    print(f"\n📋 Loading cover URLs from HAR files...")
    har_dir = Path(__file__).parent
    thumb_urls = load_har_thumb_urls(har_dir)
    print(f"  Found {len(thumb_urls)} thumb URL mappings")
    
    # 3. Scan all drama folders
    drama_dirs = sorted(MELOLO_DIR.iterdir()) if MELOLO_DIR.exists() else []
    print(f"\n📁 Scanning {len(drama_dirs)} drama folders...\n")
    
    stats = {
        'covers_downloaded': 0, 'covers_existed': 0, 'covers_failed': 0,
        'metadata_uploaded': 0, 'covers_uploaded': 0, 'total_uploaded': 0,
        'errors': 0
    }
    
    for drama_dir in drama_dirs:
        if not drama_dir.is_dir():
            continue
        
        slug = drama_dir.name
        meta_path = drama_dir / 'metadata.json'
        cover_path = drama_dir / 'cover.jpg'
        
        if not meta_path.exists():
            continue
        
        # Load metadata
        try:
            meta = json.load(open(meta_path, 'r', encoding='utf-8'))
        except:
            continue
        
        title = meta.get('title', slug)
        has_cover = cover_path.exists()
        
        # Step A: Download missing cover
        if not has_cover:
            thumb_url = thumb_urls.get(slug, '') or thumb_urls.get(meta.get('series_id', ''), '')
            if thumb_url:
                print(f"  📷 {title}: downloading cover...")
                if download_cover(thumb_url, cover_path):
                    stats['covers_downloaded'] += 1
                    has_cover = True
                    print(f"    ✅ Cover downloaded ({cover_path.stat().st_size // 1024}KB)")
                    
                    # Also update metadata with cover_url
                    meta['cover_url'] = thumb_url
                    with open(meta_path, 'w', encoding='utf-8') as f:
                        json.dump(meta, f, indent=2, ensure_ascii=False)
                else:
                    stats['covers_failed'] += 1
                    print(f"    ❌ Cover download failed")
            else:
                stats['covers_failed'] += 1
        else:
            stats['covers_existed'] += 1
        
        # Step B: Upload metadata.json to R2
        r2_meta_key = f"melolo/{slug}/metadata.json"
        if upload_file_to_r2(s3, meta_path, r2_meta_key):
            stats['metadata_uploaded'] += 1
            stats['total_uploaded'] += 1
        else:
            stats['errors'] += 1
        
        # Step C: Upload cover.jpg to R2
        if has_cover and cover_path.exists():
            r2_cover_key = f"melolo/{slug}/cover.jpg"
            if upload_file_to_r2(s3, cover_path, r2_cover_key):
                stats['covers_uploaded'] += 1
                stats['total_uploaded'] += 1
            else:
                stats['errors'] += 1
    
    # Summary
    print(f"\n{'=' * 60}")
    print(f"  REPAIR COMPLETE!")
    print(f"{'=' * 60}")
    print(f"  Covers downloaded:  {stats['covers_downloaded']}")
    print(f"  Covers existed:     {stats['covers_existed']}")
    print(f"  Covers failed:      {stats['covers_failed']}")
    print(f"  Metadata uploaded:  {stats['metadata_uploaded']}")
    print(f"  Covers uploaded:    {stats['covers_uploaded']}")
    print(f"  Total R2 uploads:   {stats['total_uploaded']}")
    print(f"  Errors:             {stats['errors']}")
    print(f"{'=' * 60}\n")


if __name__ == '__main__':
    main()
