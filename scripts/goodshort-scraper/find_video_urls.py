import json
from pathlib import Path
from collections import defaultdict

har_file = Path("har_files/batch_01.har")

print("Searching for VIDEO URLs in HAR...\n")

with open(har_file, 'r', encoding='utf-8') as f:
    har_data = json.load(f)

# Track video URLs by bookId and chapterId
video_urls = defaultdict(dict)  # bookId -> {chapterId: video_url}

# Check all relevant endpoints
video_endpoints = [
    '/hwycclientreels/chapter/load',
    '/hwycclientreels/chapter/play',
    '.m3u8'
]

found_videos = 0

for entry in har_data['log']['entries']:
    url = entry['request']['url']
    
    # Method 1: Check chapter/load responses
    if '/hwycclientreels/chapter/load' in url:
        response = entry.get('response', {})
        content = response.get('content', {})
        text = content.get('text', '')
        
        if text:
            try:
                data = json.loads(text)
                chapter_data = data.get('data', {})
                
                book_id = str(chapter_data.get('bookId', ''))
                chapter_id = str(chapter_data.get('id', chapter_data.get('chapterId', '')))
                video_url = chapter_data.get('videoUrl', chapter_data.get('videoLink', ''))
                
                # Also check cdnList
                if not video_url and 'cdnList' in chapter_data:
                    cdn_list = chapter_data.get('cdnList', [])
                    if cdn_list and len(cdn_list) > 0:
                        video_url = cdn_list[0].get('videoPath', '')
                
                if book_id and chapter_id and video_url:
                    video_urls[book_id][chapter_id] = video_url
                    found_videos += 1
                    if found_videos <= 5:
                        print(f"✅ Found video URL for book {book_id}, chapter {chapter_id}")
            except:
                pass
    
    # Method 2: Direct M3U8 URLs in requests
    elif '.m3u8' in url and 'goodshort.com' in url:
        # Extract bookId from URL pattern
        # Example: https://v3.goodshort.com/mts/books/264/31000892264/...
        try:
            parts = url.split('/')
            if 'books' in parts:
                books_idx = parts.index('books')
                if len(parts) > books_idx + 2:
                    book_id = parts[books_idx + 2]
                    # Store URL (can't determine chapter without more context)
                    print(f"  📹 Found M3U8 URL for book {book_id}: {url[:80]}...")
        except:
            pass

print(f"\n{'='*60}")
print(f"📊 RESULTS:")
print(f"  Total books with video URLs: {len(video_urls)}")
print(f"  Total video URLs found: {found_videos}")

# Show breakdown by book
for book_id, chapters in video_urls.items():
    print(f"\n  Book {book_id}: {len(chapters)} video URLs")
    for chapter_id in list(chapters.keys())[:3]:
        print(f"    - Chapter {chapter_id}: {chapters[chapter_id][:80]}...")

if found_videos == 0:
    print(f"\n⚠️  NO VIDEO URLs FOUND in HAR!")
    print("  User did not play videos during capture.")
    print("  Need to either:")
    print("    1. Re-capture with video playback")
    print("    2. Use on-demand video fetching from API")
