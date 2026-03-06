"""
Extract COMPLETE metadata from HAR file
Including: title, cover, description, genre, author, etc.
"""

import json
from pathlib import Path

def extract_complete_metadata(har_file: str):
    """Extract all drama metadata from HAR"""
    
    print(f"📂 Loading {har_file}...")
    with open(har_file, 'r', encoding='utf-8') as f:
        har = json.load(f)
    
    entries = har['log']['entries']
    
    # Dictionary to store complete metadata
    dramas_metadata = {}
    
    print("🔍 Extracting complete metadata from API calls...")
    
    for entry in entries:
        url = entry['request']['url']
        
        try:
            resp_text = entry['response']['content'].get('text', '')
            if not resp_text:
                continue
            
            data = json.loads(resp_text)
            
            # Check various endpoints for book metadata
            
            # 1. /chapter/list - has bookInfo
            if '/chapter/list' in url:
                if 'data' in data and 'bookInfo' in data['data']:
                    book_info = data['data']['bookInfo']
                    book_id = str(book_info.get('id') or book_info.get('bookId'))
                    
                    if book_id:
                        dramas_metadata[book_id] = {
                            'bookId': book_id,
                            'title': book_info.get('bookName', ''),
                            'cover': book_info.get('coverImg', ''),
                            'description': book_info.get('introduction', ''),
                            'author': book_info.get('author', ''),
                            'category': book_info.get('category', ''),
                            'tags': book_info.get('tags', []),
                            'total_episodes': book_info.get('chapterNum', 0),
                            'playCount': book_info.get('playCount', 0),
                            'score': book_info.get('score', 0)
                        }
                        print(f"  ✅ {dramas_metadata[book_id]['title']} ({book_id})")
            
            # 2. /home/index - has book list
            elif '/home/index' in url or '/recommend' in url:
                if 'data' in data:
                    # Check for book list
                    for key in ['list', 'bookList', 'recommendList']:
                        if key in data['data']:
                            books = data['data'][key]
                            if isinstance(books, list):
                                for book in books:
                                    book_id = str(book.get('id') or book.get('bookId'))
                                    if book_id and book_id not in dramas_metadata:
                                        dramas_metadata[book_id] = {
                                            'bookId': book_id,
                                            'title': book.get('bookName', ''),
                                            'cover': book.get('coverImg', ''),
                                            'description': book.get('introduction', ''),
                                            'author': book.get('author', ''),
                                            'category': book.get('category', ''),
                                            'tags': book.get('tags', []),
                                            'total_episodes': book.get('chapterNum', 0)
                                        }
                                        print(f"  ✅ {dramas_metadata[book_id]['title']} ({book_id})")
            
        except Exception as e:
            continue
    
    print(f"\n✅ Found complete metadata for {len(dramas_metadata)} dramas")
    return dramas_metadata


def update_metadata_files(metadata_dict):
    """Update existing metadata.json files with complete data"""
    
    r2_ready = Path("r2_ready")
    
    for book_id, complete_meta in metadata_dict.items():
        metadata_file = r2_ready / book_id / "metadata.json"
        
        if not metadata_file.exists():
            continue
        
        print(f"\n📝 Updating {book_id}...")
        
        # Load existing
        with open(metadata_file, 'r', encoding='utf-8') as f:
            existing = json.load(f)
        
        # Merge complete metadata
        existing['title'] = complete_meta['title']
        existing['cover'] = complete_meta['cover']
        existing['description'] = complete_meta['description']
        existing['author'] = complete_meta.get('author', '')
        existing['category'] = complete_meta.get('category', '')
        existing['tags'] = complete_meta.get('tags', [])
        existing['playCount'] = complete_meta.get('playCount', 0)
        existing['score'] = complete_meta.get('score', 0)
        
        # Save updated
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        
        print(f"  ✅ Title: {complete_meta['title']}")
        print(f"  ✅ Cover: {complete_meta['cover'][:60]}...")
        print(f"  ✅ Description: {complete_meta['description'][:80]}...")


def main():
    har_file = "HTTPToolkit_2026-02-02_23-24.har"
    
    # Extract complete metadata
    metadata = extract_complete_metadata(har_file)
    
    if not metadata:
        print("❌ No metadata found!")
        return
    
    # Update metadata files
    update_metadata_files(metadata)
    
    print("\n" + "="*60)
    print("✅ Metadata update complete!")
    print("="*60)


if __name__ == "__main__":
    main()
