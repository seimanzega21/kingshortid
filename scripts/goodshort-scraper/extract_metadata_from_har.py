"""
Extract book metadata from new HAR capture
"""
import json

har_file = "HTTPToolkit_2026-02-03_00-02.har"

print(f"📂 Loading {har_file}...")
with open(har_file, 'r', encoding='utf-8') as f:
    har = json.load(f)

entries = har['log']['entries']

print(f"✅ Total entries: {len(entries)}\n")

# Look for book info endpoints
book_info_calls = []
for entry in entries:
    url = entry['request']['url']
    
    if any(keyword in url for keyword in ['/book/info', '/book/detail', '/chapter/list', '/home/index']):
        try:
            resp_text = entry['response']['content'].get('text', '')
            if resp_text:
                data = json.loads(resp_text)
                book_info_calls.append({
                    'url': url,
                    'data': data
                })
        except:
            pass

print(f"📋 Found {len(book_info_calls)} potential book info calls\n")

# Extract all book metadata
books_found = {}

for call in book_info_calls:
    data = call['data']
    
    # Check for bookInfo in various locations
    book_info = None
    
    if 'data' in data:
        # Direct bookInfo
        if 'bookInfo' in data['data']:
            book_info = data['data']['bookInfo']
        
        # Book list
        elif 'list' in data['data']:
            items = data['data']['list']
            if isinstance(items, list):
                for item in items:
                    if 'bookName' in item or 'bookId' in item:
                        book_id = str(item.get('id') or item.get('bookId'))
                        if book_id and book_id not in books_found:
                            books_found[book_id] = {
                                'bookId': book_id,
                                'title': item.get('bookName', ''),
                                'cover': item.get('coverImg', ''),
                                'description': item.get('introduction', ''),
                                'author': item.get('author', ''),
                                'category': item.get('category', ''),
                                'tags': item.get('tags', [])
                            }
    
    if book_info:
        book_id = str(book_info.get('id') or book_info.get('bookId'))
        if book_id:
            books_found[book_id] = {
                'bookId': book_id,
                'title': book_info.get('bookName', ''),
                'cover': book_info.get('coverImg', ''),
                'description': book_info.get('introduction', ''),
                'author': book_info.get('author', ''),
                'category': book_info.get('category', ''),
                'tags': book_info.get('tags', []),
                'playCount': book_info.get('playCount', 0),
                'score': book_info.get('score', 0),
                'chapterNum': book_info.get('chapterNum', 0)
            }

print(f"📚 Books found with metadata:\n")
for book_id, meta in books_found.items():
    print(f"  {book_id}: {meta['title']}")
    print(f"    Cover: {meta['cover'][:50]}..." if meta['cover'] else "    Cover: (none)")
    print(f"    Desc: {meta['description'][:60]}..." if meta['description'] else "    Desc: (none)")
    print()

# Save extracted metadata
with open('extracted_book_metadata.json', 'w', encoding='utf-8') as f:
    json.dump(books_found, f, ensure_ascii=False, indent=2)

print(f"✅ Saved to extracted_book_metadata.json")
print(f"Total books: {len(books_found)}")
