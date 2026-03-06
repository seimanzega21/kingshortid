"""
Extract cover image URLs from HAR image requests
"""

import json
from pathlib import Path
from urllib.parse import urlparse

def extract_cover_urls_from_images():
    """Find cover images from captured image requests"""
    
    har_files = [
        "HTTPToolkit_2026-02-03_00-02.har",
        "HTTPToolkit_2026-02-02_23-24.har",
        "fresh_capture.har"
    ]
    
    # Load book IDs we care about
    target_ids = ['31001045572', '31001070612']
    
    covers_found = {}
    
    for har_file in har_files:
        if not Path(har_file).exists():
            continue
        
        print(f"\n📂 Searching {har_file} for cover images...")
        
        with open(har_file, 'r', encoding='utf-8') as f:
            har = json.load(f)
        
        entries = har['log']['entries']
        
        # Find image requests
        image_urls = []
        for entry in entries:
            url = entry['request']['url']
            
            # Check if it's an image URL
            if any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                # Check if it's from goodreels CDN
                if 'goodreels' in url or 'goodshort' in url:
                    image_urls.append(url)
        
        print(f"  Found {len(image_urls)} image URLs")
        
        # Try to match images to book IDs
        for url in image_urls:
            # Look for book IDs in URL path
            for book_id in target_ids:
                if book_id in url:
                    if book_id not in covers_found:
                        covers_found[book_id] = url
                        print(f"  ✅ {book_id}: {url[:80]}...")
    
    # If not found in URLs, look for ANY cover image pattern
    if len(covers_found) < len(target_ids):
        print(f"\n🔍 Looking for cover pattern in image URLs...")
        
        for har_file in har_files:
            if not Path(har_file).exists():
                continue
            
            with open(har_file, 'r', encoding='utf-8') as f:
                har = json.load(f)
            
            for entry in har['log']['entries']:
                url = entry['request']['url']
                
                # Look for cover-like paths
                if any(keyword in url.lower() for keyword in ['cover', 'poster', 'thumb']):
                    if 'goodreels' in url:
                        print(f"  📸 Potential cover: {url[:100]}...")
    
    return covers_found


def download_covers_for_dramas():
    """Download cover images for dramas"""
    import requests
    
    covers = extract_cover_urls_from_images()
    
    r2_ready = Path("r2_ready")
    
    for book_id, cover_url in covers.items():
        drama_folder = r2_ready / book_id
        if not drama_folder.exists():
            continue
        
        # Determine extension
        cover_ext = Path(urlparse(cover_url).path).suffix or '.jpg'
        cover_path = drama_folder / f'cover{cover_ext}'
        
        if cover_path.exists():
            print(f"\n✓ {book_id}: Cover already exists")
            continue
        
        print(f"\n📥 Downloading cover for {book_id}...")
        try:
            resp = requests.get(cover_url, timeout=15)
            resp.raise_for_status()
            
            with open(cover_path, 'wb') as f:
                f.write(resp.content)
            
            size_kb = len(resp.content) / 1024
            print(f"  ✅ Saved: {cover_path.name} ({size_kb:.1f} KB)")
            
            # Update metadata with cover URL
            metadata_file = drama_folder / 'metadata.json'
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                metadata['cover'] = cover_url
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        except Exception as e:
            print(f"  ❌ Error: {e}")


if __name__ == "__main__":
    download_covers_for_dramas()
