import json
from pathlib import Path

har_file = Path("har_files/batch_01.har")

with open(har_file, 'r', encoding='utf-8') as f:
    har_data = json.load(f)

print("Checking for book/drama data in HAR...\n")

found_dramas = 0
for entry in har_data['log']['entries']:
    url = entry['request']['url']
    
    if '/hwycclientreels/chapter/list' in url or '/hwycclientreels/book/' in url or '/hwycclientreels/home/' in url:
        response = entry.get('response', {})
        content = response.get('content', {})
        text = content.get('text', '')
        
        if not text:
            continue
        
        try:
            data = json.loads(text)
            
            # Check various possible paths for book data
            books = []
            if isinstance(data.get('data',{}), dict):
                if data['data'].get('list'):
                    books = data['data']['list']
                elif data['data'].get('books'):
                    books = data['data']['books']
            
            for book in books:
                if isinstance(book, dict) and book.get('bookId'):
                    found_dramas += 1
                    print(f"\nDrama {found_dramas}:")
                    print(f"  BookID: {book.get('bookId')}")
                    print(f"  Title: {book.get('name', book.get('bookName', 'N/A'))}")
                    print(f"  Chapters: {book.get('chapterCount', book.get('sections', 0))}")
                    
                    # Check for embedded chapters
                    chapters = book.get('chapterList', book.get('sections', []))
                    if chapters:
                        print(f"  Has {len(chapters)} chapters in response")
                    
                    if found_dramas >=5:  # Show first 5
                        break
            
            if found_dramas >= 5:
                break
                
        except:
            pass

print(f"\n\nTotal dramas found: {found_dramas}")
