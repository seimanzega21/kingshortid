"""
WEB METADATA SCRAPER
====================
Fetch book metadata from GoodShort web API using book IDs from video URLs
This bypasses the Frida capture limitation for metadata
"""
import json
import requests
from pathlib import Path
import time

# GoodShort might have web API or we can try common endpoints
BASE_URLS = [
    "https://api-akm.goodreels.com/hwycclientreels",
    "https://www.goodreels.com/api",
]

def get_book_ids_from_videos():
    """Extract unique book IDs from captured video URLs"""
    video_file = Path('scraped_data/complete_capture.json')
    if not video_file.exists():
        video_file = Path('scraped_data/extended_capture.json')
    
    if not video_file.exists():
        print("[!] No capture file found!")
        return []
    
    with open(video_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    videos = data.get('videoUrls', [])
    if not videos:
        videos = [x for x in data if x.get('type') == 'video_url']
    
    book_ids = set()
    for v in videos:
        url = v.get('url', '') if isinstance(v, dict) else v
        # Extract book ID from URL: /books/xxx/BOOKID/...
        if '/books/' in url:
            parts = url.split('/')
            for i, p in enumerate(parts):
                if p == 'books' and i + 2 < len(parts):
                    book_ids.add(parts[i + 2])
    
    return sorted(list(book_ids))

def try_fetch_book_web(book_id):
    """Try to fetch book metadata from web sources"""
    metadata = {
        'bookId': book_id,
        'title': None,
        'cover': None,
        'description': None,
        'genre': None,
    }
    
    # Try web page (might have SSR data)
    try:
        url = f"https://www.goodreels.com/book/{book_id}"
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        if response.status_code == 200:
            text = response.text
            
            # Try to find title in HTML
            if '<title>' in text:
                start = text.find('<title>') + 7
                end = text.find('</title>', start)
                if end > start:
                    title = text[start:end].strip()
                    if title and 'GoodReels' not in title:
                        metadata['title'] = title
            
            # Look for JSON data in script tags
            if '"bookName"' in text or '"name"' in text:
                import re
                # Find JSON in script
                json_match = re.search(r'<script[^>]*>([^<]+bookName[^<]+)</script>', text)
                if json_match:
                    try:
                        data = json.loads(json_match.group(1))
                        metadata['title'] = data.get('bookName', data.get('name'))
                        metadata['cover'] = data.get('coverUrl', data.get('cover'))
                        metadata['description'] = data.get('description', data.get('intro'))
                    except:
                        pass
            
            # Look for Open Graph tags
            if 'og:title' in text:
                import re
                og_title = re.search(r'property="og:title"\s+content="([^"]+)"', text)
                if og_title:
                    metadata['title'] = og_title.group(1)
                og_image = re.search(r'property="og:image"\s+content="([^"]+)"', text)
                if og_image:
                    metadata['cover'] = og_image.group(1)
                og_desc = re.search(r'property="og:description"\s+content="([^"]+)"', text)
                if og_desc:
                    metadata['description'] = og_desc.group(1)
                    
    except Exception as e:
        print(f"    Web error: {e}")
    
    return metadata

def create_placeholder_metadata(book_ids):
    """Create placeholder metadata structure for book IDs"""
    metadata = {}
    
    for book_id in book_ids:
        metadata[book_id] = {
            'bookId': book_id,
            'title': f"GoodShort Drama {book_id}",  # Placeholder
            'cover': None,
            'description': f"Scraped from GoodShort. Book ID: {book_id}",
            'genre': 'Drama',
            'source': 'goodshort',
            'needsUpdate': True  # Flag for manual update
        }
    
    return metadata

def main():
    print("=" * 60)
    print("WEB METADATA SCRAPER")
    print("=" * 60)
    
    # Get book IDs from videos
    book_ids = get_book_ids_from_videos()
    print(f"\nBook IDs from videos: {len(book_ids)}")
    for bid in book_ids:
        print(f"  - {bid}")
    
    if not book_ids:
        print("\n[!] No book IDs found!")
        return
    
    # Try to fetch from web
    print("\n[*] Attempting web metadata fetch...")
    
    metadata = {}
    for book_id in book_ids:
        print(f"\n[{book_id}]")
        
        meta = try_fetch_book_web(book_id)
        
        if meta['title']:
            print(f"  ✓ Title: {meta['title']}")
            print(f"  ✓ Cover: {meta['cover'][:50] if meta['cover'] else 'N/A'}...")
            metadata[book_id] = meta
        else:
            print(f"  ✗ No web data found - using placeholder")
            metadata[book_id] = {
                'bookId': book_id,
                'title': f"GoodShort Drama {book_id[-6:]}",
                'cover': None,
                'description': f"Scraped drama. Original ID: {book_id}",
                'genre': 'Drama',
                'source': 'goodshort',
                'needsUpdate': True
            }
        
        time.sleep(0.5)  # Rate limit
    
    # Save
    output_path = Path('scraped_data/books_metadata.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print("METADATA SAVED")
    print("=" * 60)
    print(f"\nFile: {output_path}")
    print(f"Books: {len(metadata)}")
    
    with_title = sum(1 for m in metadata.values() if m.get('title') and not m.get('needsUpdate'))
    print(f"With real titles: {with_title}")
    print(f"With placeholders: {len(metadata) - with_title}")
    
    if any(m.get('needsUpdate') for m in metadata.values()):
        print("\n[!] Some books have placeholder metadata.")
        print("    You can manually update scraped_data/books_metadata.json")
        print("    Or capture metadata from app when scrolling home page slowly.")

if __name__ == '__main__':
    main()
