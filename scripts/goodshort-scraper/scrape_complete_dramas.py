#!/usr/bin/env python3
"""
Complete Drama Scraper with R2 Upload
======================================

Downloads complete drama data (cover, metadata, episodes) and uploads to R2.

Output structure:
  scraped_dramas/
    └── {Drama Title}/
        ├── cover.jpg
        ├── metadata.json
        └── episodes.json

Then uploads to R2:
  r2://bucket/dramas/{drama_id}/cover.jpg
  r2://bucket/dramas/{drama_id}/metadata.json
  r2://bucket/dramas/{drama_id}/episodes.json
"""

import requests
import json
import boto3
from pathlib import Path
from PIL import Image
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent
OUTPUT_BASE = SCRIPT_DIR / "scraped_dramas"
OUTPUT_BASE.mkdir(exist_ok=True)

# R2 Configuration
R2_ACCOUNT_ID = "your_account_id"
R2_ACCESS_KEY = "your_access_key"
R2_SECRET_KEY = "your_secret_key"
R2_BUCKET = "kingshortid"

HEADERS = {
    'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 11; sdk_gphone_x86_64 Build/RSR1.240422.006)',
    'Host': 'acf.goodreels.com',
    'Connection': 'Keep-Alive',
    'Accept-Encoding': 'gzip'
}

def init_r2_client():
    """Initialize R2 S3-compatible client."""
    return boto3.client(
        's3',
        endpoint_url=f'https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        region_name='auto'
    )

def load_captured_data():
    """Load captured data from Frida."""
    # For now, load from manual export
    # TODO: Auto-pull from device
    
    data_file = SCRIPT_DIR / "captured_data.json"
    
    if not data_file.exists():
        print("❌ No captured data found!")
        print("Please run Frida, browse dramas, then:")
        print("1. In Frida console: rpc.exports.export()")
        print("2. Copy output to captured_data.json")
        return None
    
    with open(data_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def sanitize_folder_name(title: str) -> str:
    """Clean title for folder name."""
    import re
    title = re.sub(r'[<>:"/\\|?*]', '', title)
    return title.strip() or 'Unknown Drama'

def download_cover(url: str, output_path: Path) -> bool:
    """Download cover and validate it's a portrait poster."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        
        # Save temp
        temp_path = output_path.parent / "temp_cover.jpg"
        with open(temp_path, 'wb') as f:
            f.write(response.content)
        
        # Validate
        img = Image.open(temp_path)
        width, height = img.size
        
        is_portrait = height > width
        is_quality = len(response.content) > 50000
        
        if is_portrait and is_quality:
            # Convert to RGB if needed
            if img.mode == 'RGBA':
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[3])
                img = rgb_img
            
            img.save(output_path, 'JPEG', quality=95)
            temp_path.unlink()
            return True
        else:
            temp_path.unlink()
            return False
            
    except Exception as e:
        print(f"      ❌ Download failed: {e}")
        return False

def scrape_and_upload_dramas(upload_to_r2=True):
    """Main scraping & upload pipeline."""
    
    print(f"\n{'='*70}")
    print("🎬 Complete Drama Scraper with R2 Upload")
    print(f"{'='*70}\n")
    
    # Load captured data
    data = load_captured_data()
    if not data:
        return
    
    dramas = data.get('dramas', {})
    
    print(f"[*] Found {len(dramas)} dramas to process\n")
    
    # Initialize R2
    r2_client = None
    if upload_to_r2:
        try:
            r2_client = init_r2_client()
            print("[✓] R2 client initialized\n")
        except Exception as e:
            print(f"[!] R2 init failed: {e}")
            print("[!] Will skip R2 upload\n")
            upload_to_r2 = False
    
    successful = 0
    failed = 0
    
    for book_id, drama in dramas.items():
        title = drama.get('title', f'Drama {book_id}')
        
        print(f"{'─'*70}")
        print(f"📚 {title}")
        print(f"   ID: {book_id}")
        
        # Create drama folder
        folder_name = sanitize_folder_name(title)
        drama_folder = OUTPUT_BASE / folder_name
        drama_folder.mkdir(exist_ok=True)
        
        # 1. Download cover
        cover_path = drama_folder / "cover.jpg"
        cover_urls = drama.get('coverUrls', [])
        
        if not cover_path.exists() and cover_urls:
            print(f"   🖼️  Downloading cover...")
            for url in cover_urls:
                if download_cover(url, cover_path):
                    print(f"      ✅ Saved: cover.jpg")
                    break
        elif cover_path.exists():
            print(f"   ⏭️  Cover exists")
        
        # 2. Save metadata
        metadata_path = drama_folder / "metadata.json"
        metadata = {
            'bookId': book_id,
            'title': drama.get('title'),
            'description': drama.get('description'),
            'genre': drama.get('genre'),
            'tags': drama.get('tags', []),
            'totalEpisodes': drama.get('totalEpisodes', 0),
            'author': drama.get('author'),
            'coverUrl': cover_urls[0] if cover_urls else None,
            'scrapedAt': datetime.now().isoformat()
        }
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        print(f"   📝 Saved: metadata.json")
        
        # 3. Save episodes
        episodes_path = drama_folder / "episodes.json"
        episodes = drama.get('episodes', [])
        hls_urls = drama.get('hlsUrls', [])
        
        # Enhance episodes with HLS URLs
        for i, ep in enumerate(episodes):
            if i < len(hls_urls):
                ep['hlsUrl'] = hls_urls[i]
        
        with open(episodes_path, 'w', encoding='utf-8') as f:
            json.dump(episodes, f, indent=2, ensure_ascii=False)
        print(f"   📺 Saved: episodes.json ({len(episodes)} episodes)")
        
        # 4. Upload to R2
        if upload_to_r2 and r2_client and cover_path.exists():
            try:
                print(f"   ☁️  Uploading to R2...")
                
                # Upload cover
                r2_cover_key = f"dramas/{book_id}/cover.jpg"
                r2_client.upload_file(
                    str(cover_path),
                    R2_BUCKET,
                    r2_cover_key,
                    ExtraArgs={'ContentType': 'image/jpeg'}
                )
                
                # Upload metadata
                r2_meta_key = f"dramas/{book_id}/metadata.json"
                r2_client.upload_file(
                    str(metadata_path),
                    R2_BUCKET,
                    r2_meta_key,
                    ExtraArgs={'ContentType': 'application/json'}
                )
                
                # Upload episodes
                r2_ep_key = f"dramas/{book_id}/episodes.json"
                r2_client.upload_file(
                    str(episodes_path),
                    R2_BUCKET,
                    r2_ep_key,
                    ExtraArgs={'ContentType': 'application/json'}
                )
                
                print(f"      ✅ Uploaded to R2: dramas/{book_id}/")
                successful += 1
                
            except Exception as e:
                print(f"      ❌ R2 upload failed: {e}")
                failed += 1
        else:
            successful += 1
        
        print()
    
    print(f"{'='*70}")
    print("✅ SCRAPING COMPLETE!")
    print(f"{'='*70}\n")
    print(f"✅ Successfully processed: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"\n📁 Local: {OUTPUT_BASE}/")
    if upload_to_r2:
        print(f"☁️  R2: s3://{R2_BUCKET}/dramas/")
    print()

if __name__ == "__main__":
    # For now, don't upload to R2 (need credentials)
    scrape_and_upload_dramas(upload_to_r2=False)
