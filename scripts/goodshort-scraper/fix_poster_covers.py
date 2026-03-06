"""
Find and download POSTER format covers (vertical/portrait)
"""

import json
from pathlib import Path
from urllib.parse import urlparse
import requests

def find_poster_urls():
    """Search HAR files for vertical poster images"""
    
    har_files = [
        "HTTPToolkit_2026-02-03_00-02.har",
        "HTTPToolkit_2026-02-02_23-24.har",
        "fresh_capture.har"
    ]
    
    target_ids = ['31001045572', '31001070612']
    poster_candidates = {bid: [] for bid in target_ids}
    
    for har_file in har_files:
        if not Path(har_file).exists():
            continue
        
        print(f"📂 Searching {har_file}...")
        
        with open(har_file, 'r', encoding='utf-8') as f:
            har = json.load(f)
        
        for entry in har['log']['entries']:
            url = entry['request']['url']
            
            # Look for image URLs from goodreels CDN
            if not any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                continue
            
            if 'goodreels' not in url:
                continue
            
            # Look for poster-like paths
            url_lower = url.lower()
            
            # Check for each book ID
            for book_id in target_ids:
                if book_id in url:
                    # Prioritize URLs with "poster" or "cover" in path
                    priority = 0
                    if 'poster' in url_lower:
                        priority = 3
                    elif 'cover' in url_lower:
                        priority = 2
                    elif book_id in url:
                        priority = 1
                    
                    if priority > 0:
                        poster_candidates[book_id].append((priority, url))
    
    # Sort by priority and deduplicate
    results = {}
    for book_id, candidates in poster_candidates.items():
        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            results[book_id] = candidates[0][1]
            print(f"✅ {book_id}: {candidates[0][1][:80]}...")
        else:
            print(f"⚠️  {book_id}: No poster found")
    
    return results


def download_posters():
    """Download poster format covers"""
    
    posters = find_poster_urls()
    r2_ready = Path("r2_ready")
    
    for book_id, poster_url in posters.items():
        drama_folder = r2_ready / book_id
        if not drama_folder.exists():
            continue
        
        # Remove old cover
        for old_cover in drama_folder.glob("cover.*"):
            old_cover.unlink()
            print(f"🗑️  Removed old cover: {old_cover.name}")
        
        # Download new poster
        ext = Path(urlparse(poster_url).path).suffix or '.jpg'
        poster_path = drama_folder / f'cover{ext}'
        
        print(f"📥 Downloading poster for {book_id}...")
        try:
            resp = requests.get(poster_url, timeout=15)
            resp.raise_for_status()
            
            with open(poster_path, 'wb') as f:
                f.write(resp.content)
            
            size_kb = len(resp.content) / 1024
            print(f"  ✅ Saved: {poster_path.name} ({size_kb:.1f} KB)")
            
            # Update metadata
            metadata_file = drama_folder / 'metadata.json'
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                metadata['cover'] = poster_url
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        except Exception as e:
            print(f"  ❌ Error: {e}")


if __name__ == "__main__":
    download_posters()
