#!/usr/bin/env python3
"""
Direct Cover Download - Using Captured CDN Pattern
===================================================

Downloads covers using the real CDN pattern observed from Frida interception.
URL Pattern: https://acf.goodreels.com/videobook/{bookId}/{date}/cover-{hash}.jpg
"""

import requests
from pathlib import Path
import json

SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "cdn_covers_final"
METADATA_FILE = SCRIPT_DIR / "final_production" / "production_metadata.json"

OUTPUT_DIR.mkdir(exist_ok=True)

# Real headers from app
HEADERS = {
    'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 11; sdk_gphone_x86_64 Build/RSR1.240422.006)',
    'Host': 'acf.goodreels.com',
    'Connection': 'Keep-Alive',
    'Accept-Encoding': 'gzip'
}

# Known cover URL from Frida capture
KNOWN_URLS = {
    '31000860396': 'https://acf.goodreels.com/videobook/31000860396/202509/cover-nrSb55zugf.jpg'
}

def get_book_ids():
    """Get book IDs from existing metadata."""
    book_ids = []
    
    if METADATA_FILE.exists():
        with open(METADATA_FILE, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            book_ids = list(metadata.keys())
    
    # Add known IDs
    book_ids.extend(KNOWN_URLS.keys())
    
    return list(set(book_ids))

def try_download_cover(book_id: str) -> bytes:
    """Try to download cover using known patterns."""
    
    # If we have known URL, use it
    if book_id in KNOWN_URLS:
        try:
            url = KNOWN_URLS[book_id]
            print(f"      ✅ Using known URL")
            response = requests.get(url, headers=HEADERS, timeout=30)
            if response.status_code == 200:
                return response.content
        except:
            pass
    
    # Try common patterns observed
    year_months = ['202601', '202509', '202512', '202411']
    
    for ym in year_months:
       # Pattern 1: /videobook/{bookId}/{yearmonth}/cover-{hash}.jpg
        # We don't know the hash, so try common ones
        common_hashes = [
            'default',
            f'{book_id}',
            'cover',
            'poster'
        ]
        
        for hash_val in common_hashes:
            url = f"https://acf.goodreels.com/videobook/{book_id}/{ym}/cover-{hash_val}.jpg"
            
            try:
                response = requests.get(url, headers=HEADERS, timeout=5)
                if response.status_code == 200 and len(response.content) > 5000:
                    return response.content
            except:
                pass
    
    # Pattern 2: Direct /videobook/{bookId}/cover.jpg
    try:
        url = f"https://acf.goodreels.com/videobook/{book_id}/cover.jpg"
        response = requests.get(url, headers=HEADERS, timeout=5)
        if response.status_code == 200:
            return response.content
    except:
        pass
    
    return None

def download_covers():
    """Download covers for all known book IDs."""
    
    print(f"\n{'='*70}")
    print("🎯 CDN Cover Downloader - Using Real Captured Patterns")
    print(f"{'='*70}\n")
    
    book_ids = get_book_ids()
    
    print(f"[*] Found {len(book_ids)} book IDs to process\n")
    
    downloaded = 0
    failed = 0
    
    for book_id in book_ids:
        print(f"{'─'*70}")
        print(f"📚 Book ID: {book_id}")
        
        cover_path = OUTPUT_DIR / f"{book_id}.jpg"
        
        if cover_path.exists():
            print(f"   ⏭️  Already exists")
            continue
        
        print(f"   🌐 Downloading from CDN...")
        
        cover_data = try_download_cover(book_id)
        
        if cover_data:
            with open(cover_path, 'wb') as f:
                f.write(cover_data)
            
            print(f"   ✅ SUCCESS: {len(cover_data):,} bytes")
            downloaded += 1
        else:
            print(f"   ❌ All patterns failed")
            failed += 1
        
        print()
    
    print(f"{'='*70}")
    print("✅ DOWNLOAD COMPLETE!")
    print(f"{'='*70}\n")
    print(f"📊 Downloaded: {downloaded}")
    print(f"❌ Failed: {failed}")
    print(f"\n📁 Covers: {OUTPUT_DIR}/\n")

if __name__ == "__main__":
    download_covers()
