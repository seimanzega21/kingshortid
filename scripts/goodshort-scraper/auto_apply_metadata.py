"""
Auto-apply metadata from all_books_metadata.json to drama folders
"""

import json
from pathlib import Path

def auto_apply_metadata():
    """Automatically apply extracted metadata"""
    
    # Load extracted metadata
    metadata_file = Path("all_books_metadata.json")
    
    if not metadata_file.exists():
        print("❌ all_books_metadata.json not found!")
        print("Run deep_search_metadata.py first")
        return
    
    with open(metadata_file, 'r', encoding='utf-8') as f:
        all_books = json.load(f)
    
    print(f"📚 Loaded metadata for {len(all_books)} books\n")
    
    # Update drama folders
    r2_ready = Path("r2_ready")
    updated_count = 0
    
    for drama_folder in r2_ready.iterdir():
        if not drama_folder.is_dir():
            continue
        
        book_id = drama_folder.name
        metadata_json = drama_folder / "metadata.json"
        
        if not metadata_json.exists():
            continue
        
        # Check if we have metadata for this book
        if book_id not in all_books:
            print(f"⚠️  {book_id}: No metadata found in HAR")
            continue
        
        book_meta = all_books[book_id]
        
        # Load existing
        with open(metadata_json, 'r', encoding='utf-8') as f:
            existing = json.load(f)
        
        # Update
        existing['title'] = book_meta.get('bookName', existing.get('title', f'Drama_{book_id}'))
        existing['cover'] = book_meta.get('coverImg', existing.get('cover', ''))
        existing['description'] = book_meta.get('introduction', existing.get('description', ''))
        existing['author'] = book_meta.get('author', existing.get('author', ''))
        existing['category'] = book_meta.get('category', existing.get('category', ''))
        existing['tags'] = book_meta.get('tags', existing.get('tags', []))
        
        # Save
        with open(metadata_json, 'w', encoding='utf-8') as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        
        print(f"✅ {book_id}")
        print(f"   Title: {existing['title']}")
        print(f"   Cover: {'✓' if existing['cover'] else '✗'}")
        print(f"   Desc: {'✓' if existing['description'] else '✗'}")
        
        # Download cover if URL exists
        if existing['cover']:
            cover_url = existing['cover']
            cover_ext = Path(cover_url).suffix or '.jpg'
            cover_path = drama_folder / f'cover{cover_ext}'
            
            if not cover_path.exists():
                try:
                    import requests
                    resp = requests.get(cover_url, timeout=10)
                    resp.raise_for_status()
                    with open(cover_path, 'wb') as f:
                        f.write(resp.content)
                    print(f"   📸 Cover downloaded: {cover_path.name}")
                except Exception as e:
                    print(f"   ⚠️  Cover download failed: {e}")
        
        print()
        updated_count += 1
    
    print("="*60)
    print(f"✅ Updated {updated_count} dramas automatically!")
    print("="*60)


if __name__ == "__main__":
    auto_apply_metadata()
