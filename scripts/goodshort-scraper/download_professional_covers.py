#!/usr/bin/env python3
"""
Professional Cover Downloader
Downloads real cover posters from captured CDN URLs
"""

import requests
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "professional_covers"
OUTPUT_DIR.mkdir(exist_ok=True)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def download_covers(covers_data_file: str = "covers_data.json"):
    """Download all covers from captured data."""
    
    print(f"\n{'='*70}")
    print("🎯 Professional Cover Downloader")
    print(f"{'='*70}\n")
    
    # Load captured data from Frida
    data_path = SCRIPT_DIR / covers_data_file
    
    if not data_path.exists():
        print(f"❌ Data file not found: {data_path}")
        print(f"\n💡 Instructions:")
        print(f"   1. Run Frida script: frida -U -f com.newreading.goodreels -l frida/cover-capturer-pro.js")
        print(f"   2. Browse 5-10 dramas in app")
        print(f"   3. In Frida console, type: exportData()")
        print(f"   4. Copy JSON output")
        print(f"   5. Save to: {data_path}")
        print(f"   6. Run this script again")
        return
    
    with open(data_path, 'r', encoding='utf-8') as f:
        dramas_data = json.load(f)
    
    print(f"[*] Found {len(dramas_data)} dramas to process\n")
    
    downloaded = 0
    failed = 0
    
    for book_id, drama in dramas_data.items():
        cover_url = drama.get('coverUrl')
        title = drama.get('title', f'Drama {book_id}')
        
        print(f"{'─'*70}")
        print(f"📚 {title}")
        print(f"   ID: {book_id}")
        
        if not cover_url:
            print(f"   ⚠️  No cover URL")
            failed += 1
            continue
        
        print(f"   🌐 Downloading...")
        
        try:
            response = requests.get(cover_url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            
            # Determine extension
            ext = '.jpg'
            content_type = response.headers.get('content-type', '')
            if 'png' in content_type:
                ext = '.png'
            elif 'webp' in content_type:
                ext = '.webp'
            
            cover_path = OUTPUT_DIR / f"{book_id}{ext}"
            with open(cover_path, 'wb') as f:
                f.write(response.content)
            
            print(f"   ✅ Saved: {cover_path.name} ({len(response.content):,} bytes)")
            downloaded += 1
            
        except Exception as e:
            print(f"   ❌ Failed: {e}")
            failed += 1
        
        print()
    
    print(f"{'='*70}")
    print("✅ DOWNLOAD COMPLETE!")
    print(f"{'='*70}\n")
    print(f"📊 Downloaded: {downloaded}")
    print(f"❌ Failed: {failed}")
    print(f"\n📁 Covers saved to: {OUTPUT_DIR}/\n")

if __name__ == "__main__":
    download_covers()
