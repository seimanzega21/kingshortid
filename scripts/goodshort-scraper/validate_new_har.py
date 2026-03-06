import json
from pathlib import Path

har_file = Path("har_files/batch_01.har")

print("Validating NEW HAR capture...\n")

with open(har_file, 'r', encoding='utf-8') as f:
    har_data = json.load(f)

entries = har_data['log']['entries']
print(f"Total requests: {len(entries)}\n")

# Look for book metadata
book_metadata_found = 0
chapter_lists_found = 0
video_urls_found = 0
unique_books = set()

for entry in entries:
    url = entry['request']['url']
    
    # Check for endpoints with book data
    if 'goodreels.com' in url:
        response = entry.get('response', {})
        content = response.get('content', {})
        text = content.get('text', '')
        
        if not text:
            continue
        
        try:
            data = json.loads(text)
            
            # Look for book list
            books = []
            if isinstance(data.get('data'), dict):
                if data['data'].get('list'):
                    books = data['data']['list']
                elif data['data'].get('books'):
                    books = data['data']['books']
            
            for book in books:
                if isinstance(book, dict):
                    book_id = book.get('bookId')
                    name = book.get('name') or book.get('bookName')
                    
                    if book_id and name:
                        book_metadata_found += 1
                        unique_books.add(str(book_id))
                        
                        if book_metadata_found <= 5:
                            print(f"Book {len(unique_books)}: {name}")
                            print(f"  BookID: {book_id}")
                            print(f"  Chapters: {book.get('chapterCount', 'N/A')}")
                    
                    # Check for chapters
                    chapters = book.get('chapterList', book.get('sections', []))
                    if chapters:
                        chapter_lists_found += 1
                        
                        # Check for video URLs
                        for ch in chapters[:1]:  # Check first chapter
                            if ch.get('videoUrl') or ch.get('videoLink'):
                                video_urls_found += 1
                                break
        except:
            pass

print(f"\n{'='*60}")
print(f"📊 VALIDATION RESULTS:")
print(f"{'='*60}")
print(f"  ✅ Unique dramas found: {len(unique_books)}")
print(f"  ✅ Books with metadata: {book_metadata_found}")
print(f"  ✅ Books with chapter lists: {chapter_lists_found}")
print(f"  ✅ Books with video URLs: {video_urls_found}")

if len(unique_books) >= 5 and book_metadata_found >= 5:
    print(f"\n🎉 HAR FILE LOOKS GOOD! Ready to process.")
else:
    print(f"\n⚠️  WARNING: May be missing data. Expected 10+ dramas.")
