"""
Search for POSTER images (with title text) from synopsis page
Different from cover images
"""

import json
from pathlib import Path
import requests

def find_synopsis_posters():
    """Search specifically for poster URLs from synopsis page"""
    
    har_file = "HTTPToolkit_2026-02-03_00-02.har"  # Latest capture with synopsis
    
    if not Path(har_file).exists():
        print(f"❌ {har_file} not found")
        return {}
    
    print(f"🔍 Analyzing {har_file} for synopsis posters...\n")
    
    with open(har_file, 'r', encoding='utf-8') as f:
        har = json.load(f)
    
    target_ids = ['31001045572', '31001070612']
    
    # Collect ALL image URLs for these books
    all_images = []
    
    for entry in har['log']['entries']:
        url = entry['request']['url']
        
        # Only images
        if not any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
            continue
        
        # Only goodreels
        if 'goodreels' not in url:
            continue
        
        # Check for book IDs
        for book_id in target_ids:
            if book_id in url:
                # Get filename
                filename = url.split('/')[-1].split('?')[0]
                path = url.split('?')[0]
                
                all_images.append({
                    'book_id': book_id,
                    'url': url,
                    'filename': filename,
                    'path': path
                })
    
    # Group by unique filename patterns
    print(f"📋 Found {len(all_images)} image URLs\n")
    
    # Show unique patterns
    unique_files = {}
    for img in all_images:
        key = img['filename']
        if key not in unique_files:
            unique_files[key] = img
    
    print("🎨 Unique image variants:\n")
    for filename, img in sorted(unique_files.items()):
        print(f"  {img['book_id']}: {filename}")
        print(f"    {img['url'][:100]}...")
        print()
    
    # Try to identify poster vs cover
    posters = {}
    covers = {}
    
    for img in all_images:
        filename_lower = img['filename'].lower()
        
        # Different filename patterns
        if 'poster' in filename_lower:
            posters[img['book_id']] = img['url']
        elif 'cover' in filename_lower:
            if img['book_id'] not in covers:  # Take first cover
                covers[img['book_id']] = img['url']
    
    print("\n" + "="*70)
    print("📊 CATEGORIZED:")
    print("="*70)
    
    for book_id in target_ids:
        print(f"\n{book_id}:")
        if book_id in posters:
            print(f"  ✅ POSTER: {posters[book_id][:80]}...")
        else:
            print(f"  ❌ POSTER: Not found")
        
        if book_id in covers:
            print(f"  ✅ COVER: {covers[book_id][:80]}...")
        else:
            print(f"  ⚠️  COVER: Not found")
    
    # If no poster found, show all unique URLs to help identify
    if not posters:
        print("\n" + "="*70)
        print("🔎 ALL UNIQUE IMAGE URLs (to help identify poster):")
        print("="*70)
        
        for book_id in target_ids:
            print(f"\n📚 {book_id}:")
            book_images = [img for img in all_images if img['book_id'] == book_id]
            seen_urls = set()
            for img in book_images:
                if img['url'] not in seen_urls:
                    print(f"  • {img['url']}")
                    seen_urls.add(img['url'])
    
    return posters if posters else covers


def download_posters_from_synopsis():
    """Download the poster images"""
    
    poster_urls = find_synopsis_posters()
    
    if not poster_urls:
        print("\n⚠️  No poster URLs found")
        return
    
    print("\n" + "="*70)
    print("📥 DOWNLOADING POSTERS:")
    print("="*70)
    
    r2_ready = Path("r2_ready")
    
    for book_id, poster_url in poster_urls.items():
        # Find drama folder
        drama_folder = None
        for folder in r2_ready.iterdir():
            if folder.is_dir():
                metadata_file = folder / "metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                        if meta.get('bookId') == book_id:
                            drama_folder = folder
                            break
        
        if not drama_folder:
            print(f"\n⚠️  {book_id}: Folder not found")
            continue
        
        print(f"\n📁 {drama_folder.name}")
        print(f"   URL: {poster_url[:70]}...")
        
        # Download
        ext = Path(poster_url.split('?')[0]).suffix or '.jpg'
        poster_path = drama_folder / f'poster{ext}'
        
        try:
            resp = requests.get(poster_url, timeout=15)
            resp.raise_for_status()
            
            with open(poster_path, 'wb') as f:
                f.write(resp.content)
            
            size_kb = len(resp.content) / 1024
            print(f"   ✅ Downloaded: {size_kb:.1f} KB → {poster_path.name}")
            
            # Update metadata
            metadata_file = drama_folder / 'metadata.json'
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            metadata['poster'] = poster_url
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        except Exception as e:
            print(f"   ❌ Error: {e}")


if __name__ == "__main__":
    download_posters_from_synopsis()
