"""
1. Rename drama folders from book ID to title
2. Find poster covers WITH title text overlay
"""

import json
from pathlib import Path
import shutil
import re

def sanitize_filename(name):
    """Make title safe for folder name"""
    # Remove invalid chars
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    # Replace spaces with underscores
    name = name.replace(' ', '_')
    # Limit length
    return name[:100]


def rename_folders_to_titles():
    """Rename drama folders from book ID to title"""
    
    r2_ready = Path("r2_ready")
    
    for drama_folder in r2_ready.iterdir():
        if not drama_folder.is_dir():
            continue
        
        # Skip already renamed folders
        if not drama_folder.name.isdigit():
            continue
        
        metadata_file = drama_folder / "metadata.json"
        if not metadata_file.exists():
            continue
        
        # Load metadata
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        title = metadata.get('title', '')
        if not title or title.startswith('Drama_'):
            print(f"⚠️  {drama_folder.name}: No proper title, skipping")
            continue
        
        # Create safe folder name
        safe_title = sanitize_filename(title)
        new_folder = r2_ready / safe_title
        
        # Check if target exists
        if new_folder.exists():
            print(f"⚠️  {safe_title}: Folder already exists")
            continue
        
        # Rename
        print(f"📁 Renaming: {drama_folder.name} → {safe_title}")
        drama_folder.rename(new_folder)
        print(f"  ✅ Title: {title}")
    
    print("\n" + "="*60)
    print("✅ Folder renaming complete!")
    print("="*60)


def find_poster_with_title():
    """Search for poster URLs with title overlay"""
    
    har_files = [
        "HTTPToolkit_2026-02-03_00-02.har",
        "HTTPToolkit_2026-02-02_23-24.har",
        "fresh_capture.har"
    ]
    
    print("\n📸 Searching for poster variants...")
    
    # Get all image URLs for our dramas
    target_ids = ['31001045572', '31001070612']
    all_images = {bid: [] for bid in target_ids}
    
    for har_file in har_files:
        if not Path(har_file).exists():
            continue
        
        with open(har_file, 'r', encoding='utf-8') as f:
            har = json.load(f)
        
        for entry in har['log']['entries']:
            url = entry['request']['url']
            
            if not any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                continue
            
            if 'goodreels' not in url:
                continue
            
            for book_id in target_ids:
                if book_id in url:
                    all_images[book_id].append(url)
    
    print("\n📋 Image URLs found per drama:")
    for book_id, urls in all_images.items():
        print(f"\n  {book_id}: {len(urls)} images")
        # Show unique patterns
        unique_patterns = set()
        for url in urls:
            # Extract filename pattern
            if '/cover-' in url or '/poster-' in url:
                filename = url.split('/')[-1].split('?')[0]
                unique_patterns.add(filename)
        
        for pattern in sorted(unique_patterns)[:5]:
            print(f"    • {pattern}")
    
    return all_images


if __name__ == "__main__":
    # Step 1: Rename folders
    rename_folders_to_titles()
    
    # Step 2: Show available poster options
    print("\n" + "="*60)
    images = find_poster_with_title()
    print("\n💡 Checking downloaded covers...")
    print("Current covers are 'cover-XXX.jpg' (plain version)")
    print("Looking for 'poster-XXX.jpg' variant with title text...")
