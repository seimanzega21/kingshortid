#!/usr/bin/env python3
"""
Direct Cover Download - No Frida Needed
========================================

Downloads covers directly using known URL patterns and book IDs
from existing downloaded videos.
"""

import requests
from pathlib import Path
import json

SCRIPT_DIR = Path(__file__).parent
DOWNLOADS_DIR = SCRIPT_DIR / "downloads"
OUTPUT_DIR = SCRIPT_DIR / "final_production"
COVERS_DIR = OUTPUT_DIR / "covers"
METADATA_FILE = OUTPUT_DIR / "production_metadata.json"

COVERS_DIR.mkdir(parents=True, exist_ok=True)

# Cover URL pattern
COVER_URL_PATTERN = "https://acf.goodreels.com/videobook/{}/{}/cover.jpg"

HEADERS = {
    'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 11; Build/RSR1.240422.006)',
    'Host': 'acf.goodreels.com',
    'Connection': 'Keep-Alive',
    'Accept-Encoding': 'gzip'
}

def get_book_ids():
    """Extract book IDs from downloads folder."""
    book_ids = set()
    
    if DOWNLOADS_DIR.exists():
        for folder in DOWNLOADS_DIR.iterdir():
            if folder.is_dir():
                folder_name = folder.name
                book_id = folder_name.split('_')[0]
                
                if book_id.isdigit() and len(book_id) >= 11:
                    book_ids.add(book_id)
    
    return list(book_ids)

def try_cover_variants(book_id: str) -> bytes:
    """Try different cover URL patterns."""
    
    # Common patterns observed
    patterns = [
        f"https://acf.goodreels.com/videobook/202601/cover-{book_id}.jpg",
        f"https://acf.goodreels.com/videobook/{book_id}/cover.jpg",
        f"https://acf.goodreels.com/videobook/202601/{book_id}/cover.jpg",
        f"https://acf.goodreels.com/videobook/image/{book_id}.jpg"
    ]
    
    for url in patterns:
        try:
            print(f"      Trying: {url[:60]}...")
            response = requests.get(url, headers=HEADERS, timeout=10)
            
            if response.status_code == 200 and len(response.content) > 1000:
                print(f"      ✅ Success!")
                return response.content
        except:
            pass
    
    return None

def download_covers():
    """Download covers for all known book IDs."""
    
    print(f"\n{'='*70}")
    print("🎯 Direct Cover Downloader - Pattern-Based")
    print(f"{'='*70}\n")
    
    book_ids = get_book_ids()
    
    # Also check metadata file
    if METADATA_FILE.exists():
        with open(METADATA_FILE, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            book_ids.extend(metadata.keys())
    
    book_ids = list(set(book_ids))  # Remove duplicates
    
    if not book_ids:
        print("❌ No book IDs found in downloads folder")
        return
    
    print(f"[*] Found {len(book_ids)} book IDs\n")
    
    downloaded = 0
    failed = 0
    
    for book_id in book_ids:
        print(f"{'─'*70}")
        print(f"📚 Book ID: {book_id}")
        
        cover_path = COVERS_DIR / f"{book_id}.jpg"
        
        if cover_path.exists():
            print(f"   ⏭️  Cover already exists")
            continue
        
        print(f"   🌐 Downloading cover...")
        
        cover_data = try_cover_variants(book_id)
        
        if cover_data:
            with open(cover_path, 'wb') as f:
                f.write(cover_data)
            
            print(f"   ✅ Saved: {cover_path.name} ({len(cover_data):,} bytes)")
            downloaded += 1
        else:
            print(f"   ❌ All patterns failed")
            failed += 1
        
        print()
    
    print(f"{'='*70}")
    print("DOWNLOAD COMPLETE!")
    print(f"{'='*70}\n")
    print(f"✅ Downloaded: {downloaded}")
    print(f"❌ Failed: {failed}")
    print(f"\n📁 Covers: {COVERS_DIR}/\n")
    
    # Update metadata
    update_metadata_with_covers()

def update_metadata_with_covers():
    """Update production metadata with downloaded covers."""
    
    if not METADATA_FILE.exists():
        return
    
    with open(METADATA_FILE, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    updated = 0
    for book_id, drama in metadata.items():
        cover_path = COVERS_DIR / f"{book_id}.jpg"
        
        if cover_path.exists():
            drama['coverLocal'] = str(cover_path)
            drama['productionMetadata']['hasRealCover'] = True
            drama['productionMetadata']['coverSource'] = 'cdn_download'
            updated += 1
    
    if updated > 0:
        with open(METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"📝 Updated metadata for {updated} dramas\n")

if __name__ == "__main__":
    download_covers()
