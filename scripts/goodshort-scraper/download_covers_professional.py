#!/usr/bin/env python3
"""
Professional Cover Downloader from Intercepted URLs
====================================================

Downloads covers directly from CDN using URLs captured by Frida interceptor.
This is REAL scraping - network interception + automated download.
"""

import requests
import json
from pathlib import Path
import subprocess

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "professional_covers_scraped"
OUTPUT_DIR.mkdir(exist_ok=True)

# Proper headers mimicking app requests
HEADERS = {
    'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 11; sdk_gphone_x86_64 Build/RSR1.240422.006)',
    'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive'
}

def pull_cover_data():
    """Pull captured cover URLs from device."""
    device_file = "/sdcard/covers_urls.json"
    local_file = SCRIPT_DIR / "covers_urls.json"
    
    print("[*] Pulling cover data from device...")
    result = subprocess.run(
        f'adb pull {device_file} "{local_file}"',
        shell=True,
        capture_output=True,
        text=True
    )
    
    if local_file.exists():
        print(f"✅ Data pulled: {local_file}")
        return local_file
    else:
        print(f"❌ Pull failed: {result.stderr}")
        return None

def download_covers():
    """Download all captured covers."""
    
    print(f"\n{'='*70}")
    print("🎯 Professional Cover Downloader - CDN Scraping")
    print(f"{'='*70}\n")
    
    # Pull data from device
    data_file = pull_cover_data()
    
    if not data_file:
        print("\n⚠️  No data file found!")
        print("Make sure Frida interceptor is running and has captured covers")
        return
    
    # Load data
    with open(data_file, 'r', encoding='utf-8') as f:
        cover_data = json.load(f)
    
    print(f"\n[*] Found {len(cover_data)} dramas to process\n")
    
    downloaded = 0
    failed = 0
    
    for book_id, drama in cover_data.items():
        title = drama.get('title', f'Drama {book_id}')
        cover_urls = drama.get('coverUrls', [])
        
        print(f"{'─'*70}")
        print(f"📚 {title}")
        print(f"   ID: {book_id}")
        print(f"   Cover URLs: {len(cover_urls)}")
        
        if not cover_urls:
            print(f"   ⚠️  No cover URLs captured")
            failed += 1
            continue
        
        # Try each URL (usually first one is the best)
        success = False
        for i, url in enumerate(cover_urls):
            print(f"   🌐 Downloading URL {i+1}/{len(cover_urls)}...")
            print(f"      {url[:60]}...")
            
            try:
                response = requests.get(url, headers=HEADERS, timeout=30)
                response.raise_for_status()
                
                # Check if valid image
                if len(response.content) < 1000:
                    print(f"      ⚠️  Too small ({len(response.content)} bytes)")
                    continue
                
                # Determine extension
                ext = '.jpg'
                content_type = response.headers.get('content-type', '')
                if 'png' in content_type:
                    ext = '.png'
                elif 'webp' in content_type:
                    ext = '.webp'
                
                # Save
                cover_path = OUTPUT_DIR / f"{book_id}{ext}"
                with open(cover_path, 'wb') as f:
                    f.write(response.content)
                
                print(f"      ✅ Saved: {cover_path.name} ({len(response.content):,} bytes)")
                downloaded += 1
                success = True
                break
                
            except Exception as e:
                print(f"      ❌ Failed: {e}")
        
        if not success:
            failed += 1
        
        print()
    
    print(f"{'='*70}")
    print("✅ DOWNLOAD COMPLETE!")
    print(f"{'='*70}\n")
    print(f"📊 Downloaded: {downloaded}")
    print(f"❌ Failed: {failed}")
    print(f"\n📁 Covers: {OUTPUT_DIR}/\n")
    
    # Create metadata
    create_metadata(cover_data)

def create_metadata(cover_data):
    """Create production metadata from downloaded covers."""
    
    metadata = {}
    
    for book_id, drama in cover_data.items():
        cover_path = None
        for ext in ['.jpg', '.png', '.webp']:
            path = OUTPUT_DIR / f"{book_id}{ext}"
            if path.exists():
                cover_path = str(path)
                break
        
        if cover_path:
            metadata[book_id] = {
                'bookId': book_id,
                'title': drama.get('title', f'Drama {book_id}'),
                'genre': drama.get('genre', 'Drama'),
                'coverLocal': cover_path,
                'coverUrl': drama.get('coverUrls', [None])[0],
                'source': 'cdn_scraping',
                'scrapedAt': drama.get('capturedAt')
            }
    
    metadata_file = OUTPUT_DIR / 'metadata.json'
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"📝 Metadata created: {metadata_file}\n")

if __name__ == "__main__":
    download_covers()
