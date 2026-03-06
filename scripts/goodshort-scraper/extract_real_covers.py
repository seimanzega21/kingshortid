#!/usr/bin/env python3
"""
Cover Screenshot Extractor
===========================

Captures REAL drama cover posters from app UI screenshots.

How it works:
1. You screenshot drama detail page in app
2. Script crops cover poster area
3. Saves as production cover

Usage:
    1. Screenshot drama detail page
    2. Save to screenshots/ folder
    3. Run: python extract_real_covers.py
"""

from PIL import Image
from pathlib import Path
import json

SCRIPT_DIR = Path(__file__).parent
SCREENSHOTS_DIR = SCRIPT_DIR / "cover_screenshots"
OUTPUT_DIR = SCRIPT_DIR / "final_production" / "covers"
METADATA_FILE = SCRIPT_DIR / "final_production" / "production_metadata.json"

SCREENSHOTS_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

def crop_cover_from_screenshot(screenshot_path: Path, book_id: str) -> Path:
    """
    Crop cover poster area from drama detail screenshot.
    
    Cover location in GoodReels app detail page:
    - Top-left area
    - Approximately: x=50-350, y=400-700 (adjust based on screen)
    """
    try:
        img = Image.open(screenshot_path)
        width, height = img.size
        
        # Cover poster coordinates (adjust if needed)
        # Based on your screenshot: cover is on left side, below header
        left = int(width * 0.05)    # 5% from left
        top = int(height * 0.17)     # 17% from top  
        right = int(width * 0.35)    # 35% from left (30% width)
        bottom = int(height * 0.35)  # 35% from top (18% height)
        
        cover_area = img.crop((left, top, right, bottom))
        
        output_path = OUTPUT_DIR / f"{book_id}.jpg"
        cover_area.save(output_path, 'JPEG', quality=95)
        
        print(f"✅ Cropped cover: {output_path.name}")
        return output_path
        
    except Exception as e:
        print(f"❌ Crop failed: {e}")
        return None

def process_screenshots():
    """Process all screenshots in folder."""
    print(f"\n{'='*70}")
    print("📸 Real Cover Extractor - From App Screenshots")
    print(f"{'='*70}\n")
    
    screenshots = list(SCREENSHOTS_DIR.glob("*.png")) + list(SCREENSHOTS_DIR.glob("*.jpg"))
    
    if not screenshots:
        print("⚠️  No screenshots found!")
        print(f"\n💡 Instructions:")
        print(f"   1. Open drama detail page in app")
        print(f"   2. Take screenshot (show cover poster)")
        print(f"   3. Save to: {SCREENSHOTS_DIR}/")
        print(f"   4. Name format: drama_31000908479.png")
        print(f"   5. Run this script again")
        return
    
    print(f"[*] Found {len(screenshots)} screenshots\n")
    
    for screenshot in screenshots:
        print(f"{'─'*70}")
        print(f"Processing: {screenshot.name}")
        
        # Extract book ID from filename
        # Expected format: drama_31000908479.png
        filename = screenshot.stem
        book_id = ''.join(filter(str.isdigit, filename))
        
        if not book_id or len(book_id) < 11:
            print(f"⚠️  Could not extract book ID from filename")
            print(f"   Expected format: drama_31000908479.png")
            continue
        
        print(f"   Book ID: {book_id}")
        
        # Crop cover
        cover_path = crop_cover_from_screenshot(screenshot, book_id)
        
        if cover_path:
            # Update metadata
            update_metadata(book_id, str(cover_path))
        
        print()
    
    print(f"{'='*70}")
    print("✅ Extraction Complete!")
    print(f"{'='*70}\n")

def update_metadata(book_id: str, cover_path: str):
    """Update metadata with real cover path."""
    if not METADATA_FILE.exists():
        print("   ⚠️  Metadata file not found")
        return
    
    with open(METADATA_FILE, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    if book_id in metadata:
        metadata[book_id]['coverLocal'] = cover_path
        metadata[book_id]['productionMetadata']['hasRealCover'] = True
        metadata[book_id]['productionMetadata']['coverSource'] = 'screenshot_crop'
        
        with open(METADATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print("   📝 Metadata updated")

if __name__ == "__main__":
    process_screenshots()
