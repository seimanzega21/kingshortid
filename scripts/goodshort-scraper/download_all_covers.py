#!/usr/bin/env python3
"""
Download ALL Captured Cover URLs
Based on Frida interception logs, download all 22+ cover URLs
"""

import requests
from pathlib import Path
from PIL import Image

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "all_covers_scraped"
FILTERED_DIR = SCRIPT_DIR / "portrait_covers_only"

OUTPUT_DIR.mkdir(exist_ok=True)
FILTERED_DIR.mkdir(exist_ok=True)

# Proper headers
HEADERS = {
    'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 11; sdk_gphone_x86_64 Build/RSR1.240422.006)',
    'Host': 'acf.goodreels.com',
    'Connection': 'Keep-Alive',
    'Accept-Encoding': 'gzip'
}

# URLs captured from Frida (from the logs we saw)
# Pattern: https://acf.goodreels.com/videobook/{bookId}/{date}/cover-{hash}.jpg
CAPTURED_URLS = [
    'https://acf.goodreels.com/videobook/31000860396/202509/cover-nrSb55zugf.jpg',
    # Add more URLs here from Frida output
]

def download_and_filter_covers():
    """Download all URLs and filter portrait posters."""
    
    print(f"\n{'='*70}")
    print("🎯 Download ALL Captured Covers + Auto-Filter")
    print(f"{'='*70}\n")
    
    print(f"[*] Will download {len(CAPTURED_URLS)} URLs")
    print("[*] Filtering for PORTRAIT posters (height > width)\n")
    
    downloaded = 0
    portrait_count = 0
    
    for i, url in enumerate(CAPTURED_URLS, 1):
        print(f"{'─'*70}")
        print(f"📥 URL {i}/{len(CAPTURED_URLS)}")
        print(f"   {url[:65]}...")
        
        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            
            # Extract filename from URL
            filename = url.split('/')[-1]
            
            # Save ALL covers first
            all_path = OUTPUT_DIR / filename
            with open(all_path, 'wb') as f:
                f.write(response.content)
            
            print(f"   ✅ Downloaded: {len(response.content):,} bytes")
            downloaded += 1
            
            # Check if portrait (drama poster)
            try:
                img = Image.open(all_path)
                width, height = img.size
                
                print(f"   📐 Dimensions: {width}x{height}")
                
                # Portrait poster: height > width
                if height > width:
                    # Copy to filtered folder
                    portrait_path = FILTERED_DIR / filename
                    with open(portrait_path, 'wb') as f:
                        f.write(response.content)
                    
                    print(f"   🎯 PORTRAIT POSTER - Filtered! ✅")
                    portrait_count += 1
                else:
                    print(f"   ⏭️  Landscape/Square - Skipped")
                    
            except Exception as e:
                print(f"   ⚠️  Could not analyze: {e}")
            
        except Exception as e:
            print(f"   ❌ Download failed: {e}")
        
        print()
    
    print(f"{'='*70}")
    print("✅ DOWNLOAD COMPLETE!")
    print(f"{'='*70}\n")
    print(f"📥 Total Downloaded: {downloaded}")
    print(f"🎯 Portrait Posters: {portrait_count}")
    print(f"\n📁 All covers: {OUTPUT_DIR}/")
    print(f"📁 Portrait only: {FILTERED_DIR}/\n")

if __name__ == "__main__":
    download_and_filter_covers()
