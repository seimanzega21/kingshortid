"""
Parse captured data and test video downloads
"""
import json
import re
import requests
from pathlib import Path
from collections import defaultdict
from urllib.parse import urlparse

def load_captured_data():
    with open('scraped_data/extended_capture.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def parse_video_urls(data):
    """Extract and organize video URLs by book/chapter"""
    video_items = [x for x in data if x.get('type') == 'video_url']
    
    # Parse URL pattern: /mts/books/{xxx}/{bookId}/{chapterId}/{token}/{resolution}/{filename}
    pattern = r'/mts/books/\d+/(\d+)/(\d+)/([^/]+)/(\d+p)/([^/]+)'
    
    books = defaultdict(lambda: defaultdict(list))
    
    for item in video_items:
        url = item.get('url', '')
        match = re.search(pattern, url)
        if match:
            book_id = match.group(1)
            chapter_id = match.group(2)
            token = match.group(3)
            resolution = match.group(4)
            filename = match.group(5)
            
            books[book_id][chapter_id].append({
                'url': url,
                'token': token,
                'resolution': resolution,
                'filename': filename
            })
    
    return dict(books)

def parse_json_responses(data):
    """Extract book/chapter data from JSON payloads"""
    json_items = [x for x in data if x.get('type') == 'json']
    
    extracted = {
        'books': [],
        'chapters': [],
        'other': []
    }
    
    for item in json_items:
        preview = item.get('preview', '')
        
        # Try to parse as JSON
        try:
            obj = json.loads(preview)
            
            if 'bookId' in str(obj) or 'bookName' in str(obj):
                extracted['books'].append(obj)
            elif 'chapterId' in str(obj) or 'chapterName' in str(obj):
                extracted['chapters'].append(obj)
            else:
                extracted['other'].append(obj)
        except:
            pass
    
    return extracted

def test_video_download(url, output_path='test_video.ts'):
    """Test downloading a video segment"""
    print(f"\n[TEST] Downloading: {url[:80]}...")
    
    try:
        response = requests.get(url, timeout=30, stream=True)
        print(f"  Status: {response.status_code}")
        print(f"  Content-Type: {response.headers.get('Content-Type', 'unknown')}")
        print(f"  Content-Length: {response.headers.get('Content-Length', 'unknown')}")
        
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            size = Path(output_path).stat().st_size
            print(f"  Downloaded: {size:,} bytes")
            print(f"  Saved to: {output_path}")
            return True
        else:
            print(f"  [FAILED] {response.status_code}")
            return False
            
    except Exception as e:
        print(f"  [ERROR] {e}")
        return False

def main():
    print("=" * 60)
    print("PARSING CAPTURED DATA")
    print("=" * 60)
    
    data = load_captured_data()
    print(f"\nTotal items: {len(data)}")
    
    # Parse video URLs
    print("\n--- VIDEO URLs ---")
    videos = parse_video_urls(data)
    print(f"Books with videos: {len(videos)}")
    
    for book_id, chapters in list(videos.items())[:3]:
        print(f"\n  Book {book_id}:")
        for chapter_id, segments in list(chapters.items())[:2]:
            print(f"    Chapter {chapter_id}: {len(segments)} segments")
            if segments:
                print(f"      Resolution: {segments[0]['resolution']}")
                print(f"      Token: {segments[0]['token'][:20]}...")
    
    # Parse JSON
    print("\n--- JSON DATA ---")
    json_data = parse_json_responses(data)
    print(f"Book entries: {len(json_data['books'])}")
    print(f"Chapter entries: {len(json_data['chapters'])}")
    print(f"Other entries: {len(json_data['other'])}")
    
    # Save parsed data
    output_dir = Path('scraped_data/parsed')
    output_dir.mkdir(exist_ok=True)
    
    with open(output_dir / 'videos_by_book.json', 'w', encoding='utf-8') as f:
        json.dump(videos, f, indent=2)
    
    with open(output_dir / 'json_data.json', 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n[OK] Parsed data saved to {output_dir}/")
    
    # Test download first video
    print("\n--- TESTING VIDEO DOWNLOAD ---")
    all_urls = [x['url'] for x in data if x.get('type') == 'video_url']
    if all_urls:
        test_url = all_urls[0]
        success = test_video_download(test_url, 'scraped_data/test_video.ts')
        
        if success:
            print("\n[SUCCESS] Video download works!")
        else:
            print("\n[FAILED] Video download failed")
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"- Books found: {len(videos)}")
    print(f"- Total chapters: {sum(len(c) for c in videos.values())}")
    print(f"- Total video segments: {len(all_urls)}")
    print(f"- Video download: {'Working' if 'success' in dir() and success else 'Not tested'}")

if __name__ == '__main__':
    main()
