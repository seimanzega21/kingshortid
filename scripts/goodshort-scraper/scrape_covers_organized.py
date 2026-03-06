#!/usr/bin/env python3
"""
Organized Cover Scraper - Final Production Version
===================================================

Downloads covers from Frida-captured URLs and organizes by drama title.

Structure:
  scraped_dramas/
    ├── {Drama Title}/
    │   └── cover.jpg
    └── ...

Features:
- Auto-filters portrait posters only (height > width)
- Auto-filters high quality (>100KB typically)
- Saves as "cover.jpg" in drama-titled folders
- Clean, production-ready structure
"""

import requests
from pathlib import Path
from PIL import Image
import re

SCRIPT_DIR = Path(__file__).parent
OUTPUT_BASE = SCRIPT_DIR / "scraped_dramas"
OUTPUT_BASE.mkdir(exist_ok=True)

HEADERS = {
    'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 11; sdk_gphone_x86_64 Build/RSR1.240422.006)',
    'Host': 'acf.goodreels.com',
    'Connection': 'Keep-Alive',
    'Accept-Encoding': 'gzip'
}

# Captured URLs and titles from Frida interception
# Format: (url, drama_title, book_id)
CAPTURED_DRAMAS = [
    ('https://acf.goodreels.com/videobook/202508/cover-j0xXGvSlXe.jpg', 'Jatuh Cinta dengan Istri Kontrakku', '31000XXXXX'),
    ('https://acf.goodreels.com/videobook/202405/cover-xPEPIVJaGC.jpg', 'Jenderal Jadi Tukang', '31000XXXXX'),
    ('https://acf.goodreels.com/videobook/31000860396/202509/cover-nrSb55zugf.jpg', 'Drama Unknown', '31000860396'),
]

def sanitize_folder_name(title: str) -> str:
    """Clean title for folder name."""
    # Remove/replace invalid characters
    title = re.sub(r'[<>:"/\\|?*]', '', title)
    title = title.strip()
    return title if title else 'Unknown Drama'

def download_organized_covers():
    """Download and organize covers by drama title."""
    
    print(f"\n{'='*70}")
    print("🎯 Organized Cover Scraper - Final Production")
    print(f"{'='*70}\n")
    print(f"📁 Output: {OUTPUT_BASE}/\n")
    
    successful = 0
    failed = 0
    skipped = 0
    
    for url, title, book_id in CAPTURED_DRAMAS:
        print(f"{'─'*70}")
        print(f"📚 {title}")
        print(f"   ID: {book_id}")
        
        # Create drama folder
        folder_name = sanitize_folder_name(title)
        drama_folder = OUTPUT_BASE / folder_name
        drama_folder.mkdir(exist_ok=True)
        
        cover_path = drama_folder / "cover.jpg"
        
        # Skip if exists
        if cover_path.exists():
            print(f"   ⏭️  Cover exists: {folder_name}/cover.jpg")
            skipped += 1
            print()
            continue
        
        print(f"   🌐 Downloading...")
        print(f"      {url[:60]}...")
        
        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            
            # Save to temp for analysis
            temp_path = drama_folder / "temp.jpg"
            with open(temp_path, 'wb') as f:
                f.write(response.content)
            
            # Analyze
            img = Image.open(temp_path)
            width, height = img.size
            file_size = len(response.content)
            
            print(f"      📐 {width}x{height} ({file_size:,} bytes)")
            
            # Filter criteria
            is_portrait = height > width
            is_quality = file_size > 50000  # >50KB (quality posters usually >100KB)
            
            if is_portrait and is_quality:
                # Rename to cover.jpg
                temp_path.rename(cover_path)
                print(f"      ✅ SAVED: {folder_name}/cover.jpg")
                print(f"      🎯 Portrait poster confirmed!")
                successful += 1
            else:
                temp_path.unlink()  # Delete temp
                reason = "not portrait" if not is_portrait else "low quality"
                print(f"      ⏭️  Skipped: {reason}")
                failed += 1
            
        except Exception as e:
            print(f"      ❌ Failed: {e}")
            failed += 1
        
        print()
    
    print(f"{'='*70}")
    print("✅ SCRAPING COMPLETE!")
    print(f"{'='*70}\n")
    print(f"✅ Successfully scraped: {successful}")
    print(f"⏭️  Skipped (exists): {skipped}")
    print(f"❌ Failed: {failed}")
    print(f"\n📁 Browse: {OUTPUT_BASE}/\n")
    
    # List results
    if successful > 0:
        print("📚 Scraped Dramas:")
        for folder in sorted(OUTPUT_BASE.iterdir()):
            if folder.is_dir() and (folder / "cover.jpg").exists():
                print(f"   ✅ {folder.name}/cover.jpg")
        print()

if __name__ == "__main__":
    download_organized_covers()
