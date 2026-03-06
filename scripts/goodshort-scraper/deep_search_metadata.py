"""
DEEP SEARCH: Extract covers and titles from ALL HAR data
Search home feed, recommendations, and banner calls
"""

import json
from pathlib import Path
from collections import defaultdict

def deep_search_all_hars():
    """Search all HAR files for book metadata"""
    
    har_files = [
        "HTTPToolkit_2026-02-03_00-02.har",  # 314 MB - newest
        "HTTPToolkit_2026-02-02_23-24.har",  # 123 MB
        "fresh_capture.har"  # 175 MB - original
    ]
    
    all_books = {}
    
    for har_file in har_files:
        if not Path(har_file).exists():
            continue
        
        print(f"\n{'='*60}")
        print(f"📂 Analyzing: {har_file}")
        print(f"{'='*60}\n")
        
        with open(har_file, 'r', encoding='utf-8') as f:
            har = json.load(f)
        
        entries = har['log']['entries']
        
        # Search various endpoints
        endpoints_to_check = [
            '/home/index',
            '/recommend',
            '/banner',
            '/book/list',
            '/hot/rank',
            '/category',
            '/search'
        ]
        
        for entry in entries:
            url = entry['request']['url']
            
            # Check if it's a relevant endpoint
            if not any(ep in url for ep in endpoints_to_check):
                continue
            
            try:
                resp_text = entry['response']['content'].get('text', '')
                if not resp_text:
                    continue
                
                data = json.loads(resp_text)
                
                if 'data' not in data:
                    continue
                
                # Search for book arrays in response
                def find_books_recursive(obj, path=""):
                    """Recursively find book-like objects"""
                    if isinstance(obj, dict):
                        # Check if this looks like a book
                        if 'bookId' in obj or 'bookName' in obj:
                            book_id = str(obj.get('bookId') or obj.get('id', ''))
                            if book_id and (obj.get('bookName') or obj.get('coverImg')):
                                return [obj]
                        
                        # Recurse into dict
                        results = []
                        for k, v in obj.items():
                            results.extend(find_books_recursive(v, f"{path}.{k}"))
                        return results
                    
                    elif isinstance(obj, list):
                        results = []
                        for item in obj:
                            results.extend(find_books_recursive(item, f"{path}[]"))
                        return results
                    
                    return []
                
                books_in_response = find_books_recursive(data['data'])
                
                for book in books_in_response:
                    book_id = str(book.get('bookId') or book.get('id', ''))
                    if not book_id:
                        continue
                    
                    # Extract metadata
                    if book_id not in all_books or not all_books[book_id].get('bookName'):
                        all_books[book_id] = {
                            'bookId': book_id,
                            'bookName': book.get('bookName', ''),
                            'coverImg': book.get('coverImg', ''),
                            'introduction': book.get('introduction', ''),
                            'author': book.get('author', ''),
                            'category': book.get('category', ''),
                            'tags': book.get('tags', []),
                            'chapterNum': book.get('chapterNum', 0)
                        }
            
            except Exception as e:
                continue
        
        print(f"✅ Found {len([b for b in all_books.values() if b.get('bookName')])} books with metadata so far")
    
    # Filter to books with actual data
    books_with_data = {k: v for k, v in all_books.items() if v.get('bookName') or v.get('coverImg')}
    
    print(f"\n{'='*60}")
    print(f"📊 FINAL RESULTS")
    print(f"{'='*60}\n")
    print(f"Total unique books: {len(books_with_data)}")
    print(f"Books with title: {len([b for b in books_with_data.values() if b.get('bookName')])}")
    print(f"Books with cover: {len([b for b in books_with_data.values() if b.get('coverImg')])}")
    print(f"Books with description: {len([b for b in books_with_data.values() if b.get('introduction')])}")
    
    # Check our target books
    target_ids = ['31001045572', '31001070612']
    print(f"\n🎯 Target Books:")
    for book_id in target_ids:
        if book_id in books_with_data:
            book = books_with_data[book_id]
            print(f"\n  {book_id}:")
            print(f"    Title: {book.get('bookName', 'NOT FOUND')}")
            print(f"    Cover: {book.get('coverImg', 'NOT FOUND')[:60]}...")
            print(f"    Desc: {book.get('introduction', 'NOT FOUND')[:80]}...")
        else:
            print(f"\n  {book_id}: NOT FOUND")
    
    # Save all results
    with open('all_books_metadata.json', 'w', encoding='utf-8') as f:
        json.dump(books_with_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Saved to all_books_metadata.json")
    
    return books_with_data


if __name__ == "__main__":
    books = deep_search_all_hars()
