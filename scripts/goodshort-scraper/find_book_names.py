import json
from pathlib import Path

har_file = Path("har_files/batch_01.har")

with open(har_file, 'r', encoding='utf-8') as f:
    har_data = json.load(f)

print("Looking for book DETAIL/INFO endpoints...\n")

# Check for any endpoints that might have book metadata
book_endpoints = [
    '/hwycclientreels/book/',
    '/hwycclientreels/home/',
    'foru/introduction',
    'quick/open'
]

found_books = {}

for entry in har_data['log']['entries']:
    url = entry['request']['url']
    
    # Check if any book endpoint
    if any(ep in url for ep in book_endpoints):
        response = entry.get('response', {})
        content = response.get('content', {})
        text = content.get('text', '')
        
        if not text:
            continue
        
        try:
            data = json.loads(text)
            
            # Look for book data with NAME
            if isinstance(data.get('data'), dict):
                book_data = data['data']
                
                # Check various structures
                if 'book' in book_data:
                    book = book_data['book']
                elif 'info' in book_data:
                    book = book_data['info']
                else:
                    book = book_data
                
                name = book.get('name') or book.get('bookName') or book.get('title')
                book_id = book.get('bookId') or book.get('id')
                
                if name and book_id:
                    if book_id not in found_books:
                        found_books[book_id] = name
                        print(f"✅ Book: {name}")
                        print(f"   ID: {book_id}")
                        print(f"   From: {url.split('?')[0]}")
                        print()
        except:
            pass

print(f"\n{'='*60}")
print(f"Total unique books with NAME found: {len(found_books)}")

if len(found_books) == 0:
    print("\n⚠️  NO BOOK METADATA FOUND!")
    print("   Drama NAMES are missing from capture.")
    print("   We only have chapter IDs and BookIDs.")
