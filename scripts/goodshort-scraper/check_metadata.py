"""
Check what metadata is available in captured data
"""
import json

def analyze_metadata():
    with open('scraped_data/extended_capture.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("=" * 60)
    print("METADATA ANALYSIS")
    print("=" * 60)
    
    # Get all JSON and response items
    jsons = [x for x in data if x.get('type') == 'json']
    responses = [x for x in data if x.get('type') == 'response']
    videos = [x for x in data if x.get('type') == 'video_url']
    
    print(f"\nCaptured items:")
    print(f"  JSON payloads: {len(jsons)}")
    print(f"  Retrofit responses: {len(responses)}")
    print(f"  Video URLs: {len(videos)}")
    
    # Check for book metadata in JSON
    print("\n" + "=" * 60)
    print("SEARCHING FOR BOOK METADATA...")
    print("=" * 60)
    
    metadata_found = {
        'bookName': False,
        'bookTitle': False,
        'title': False,
        'cover': False,
        'coverUrl': False,
        'description': False,
        'synopsis': False,
        'genre': False,
        'category': False,
        'author': False,
        'chapterList': False,
        'episodeList': False,
    }
    
    all_text = ""
    for j in jsons:
        preview = j.get('preview', '')
        all_text += preview + "\n"
    
    for r in responses:
        body = r.get('body', '')
        all_text += body + "\n"
    
    for key in metadata_found:
        if key.lower() in all_text.lower():
            metadata_found[key] = True
    
    print("\nMetadata fields found:")
    for key, found in metadata_found.items():
        status = "✓ YES" if found else "✗ NO"
        print(f"  {key}: {status}")
    
    # Show sample content
    print("\n" + "=" * 60)
    print("SAMPLE JSON CONTENT")
    print("=" * 60)
    
    for j in jsons[:5]:
        preview = j.get('preview', '')
        if 'book' in preview.lower() or 'title' in preview.lower():
            print(f"\n{preview[:500]}")
            print("-" * 40)
    
    # Check video URLs for book IDs
    print("\n" + "=" * 60)
    print("VIDEO URL BOOK IDs")
    print("=" * 60)
    
    book_ids = set()
    for v in videos:
        url = v.get('url', '')
        # Extract book ID from URL pattern: /books/xxx/BOOKID/...
        parts = url.split('/')
        for i, p in enumerate(parts):
            if p == 'books' and i+2 < len(parts):
                book_ids.add(parts[i+2])
    
    print(f"\nUnique book IDs from video URLs: {len(book_ids)}")
    for bid in sorted(book_ids):
        print(f"  - {bid}")
    
    # Conclusion
    print("\n" + "=" * 60)
    print("CONCLUSION")
    print("=" * 60)
    
    has_metadata = any([
        metadata_found['bookName'],
        metadata_found['title'],
        metadata_found['cover'],
        metadata_found['description'],
    ])
    
    if has_metadata:
        print("\n✓ Some metadata IS captured!")
    else:
        print("\n✗ Book metadata NOT captured!")
        print("\n  REASON: Current hooks only capture:")
        print("    - Video segment URLs")
        print("    - JSONObject for API success/error")
        print("    - Retrofit response status")
        print("\n  MISSING: Need to capture /home/index or /book/detail responses")
        print("           which contain title, cover, description, genre, etc.")

if __name__ == '__main__':
    analyze_metadata()
