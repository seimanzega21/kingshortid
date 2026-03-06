"""
Search for poster images WITH title text overlay
Look for different naming patterns
"""

import json
from pathlib import Path
import requests

def search_poster_variants():
    """Deep search for poster variants in HAR"""
    
    har_files = [
        "HTTPToolkit_2026-02-03_00-02.har",
        "HTTPToolkit_2026-02-02_23-24.har",
        "fresh_capture.har"
    ]
    
    target_ids = ['31001045572', '31001070612']
    
    print("🔍 Deep search for ALL image variants...\n")
    
    image_urls_by_book = {bid: {} for bid in target_ids}
    
    for har_file in har_files:
        if not Path(har_file).exists():
            continue
        
        print(f"📂 Analyzing {har_file}...")
        
        with open(har_file, 'r', encoding='utf-8') as f:
            har = json.load(f)
        
        for entry in har['log']['entries']:
            url = entry['request']['url']
            
            # Image files only
            if not any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                continue
            
            # GoodReels CDN only
            if 'goodreels' not in url:
                continue
            
            # Check for book IDs
            for book_id in target_ids:
                if book_id in url:
                    # Extract filename
                    parts = url.split('?')[0].split('/')
                    filename = parts[-1] if parts else url
                    
                    # Categorize
                    if 'poster' in filename.lower():
                        category = 'POSTER (with text)'
                    elif 'cover' in filename.lower():
                        category = 'COVER (plain)'
                    elif 'thumb' in filename.lower():
                        category = 'THUMBNAIL'
                    else:
                        category = 'OTHER'
                    
                    if category not in image_urls_by_book[book_id]:
                        image_urls_by_book[book_id][category] = []
                    
                    if url not in image_urls_by_book[book_id][category]:
                        image_urls_by_book[book_id][category].append(url)
    
    # Display findings
    print("\n" + "="*70)
    print("📊 IMAGE VARIANTS FOUND:")
    print("="*70)
    
    for book_id, categories in image_urls_by_book.items():
        print(f"\n📚 Book ID: {book_id}")
        
        if not categories:
            print("  ❌ No images found")
            continue
        
        for category, urls in sorted(categories.items()):
            print(f"\n  {category}: {len(urls)} URL(s)")
            for url in urls[:3]:  # Show first 3
                print(f"    • {url[:90]}...")
    
    # Try to download poster variants
    print("\n" + "="*70)
    print("📥 DOWNLOADING POSTER VARIANTS (if found):")
    print("="*70)
    
    r2_ready = Path("r2_ready")
    
    for book_id, categories in image_urls_by_book.items():
        # Look for drama folder (renamed to title)
        drama_folders = []
        for folder in r2_ready.iterdir():
            if folder.is_dir():
                metadata_file = folder / "metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                        if meta.get('bookId') == book_id:
                            drama_folders.append(folder)
        
        if not drama_folders:
            print(f"\n⚠️  {book_id}: Folder not found")
            continue
        
        drama_folder = drama_folders[0]
        
        # Prefer POSTER, fallback to COVER
        poster_url = None
        if 'POSTER (with text)' in categories and categories['POSTER (with text)']:
            poster_url = categories['POSTER (with text)'][0]
            print(f"\n✅ {drama_folder.name}: Found POSTER variant!")
        elif 'COVER (plain)' in categories and categories['COVER (plain)']:
            poster_url = categories['COVER (plain)'][0]
            print(f"\n⚠️  {drama_folder.name}: Only COVER available (no text variant found)")
        
        if poster_url:
            # Download
            ext = Path(poster_url.split('?')[0]).suffix or '.jpg'
            poster_path = drama_folder / f'poster{ext}'
            
            try:
                resp = requests.get(poster_url, timeout=15)
                resp.raise_for_status()
                
                with open(poster_path, 'wb') as f:
                    f.write(resp.content)
                
                size_kb = len(resp.content) / 1024
                print(f"  📥 Downloaded: {size_kb:.1f} KB → {poster_path.name}")
                
                # Update metadata
                metadata_file = drama_folder / 'metadata.json'
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                metadata['poster'] = poster_url
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            except Exception as e:
                print(f"  ❌ Download error: {e}")


if __name__ == "__main__":
    search_poster_variants()
