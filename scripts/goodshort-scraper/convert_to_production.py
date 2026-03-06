#!/usr/bin/env python3
"""
Convert complete_capture.json to production data format
Extract real drama metadata from videoUrls
"""

import json
from pathlib import Path
from collections import defaultdict

SCRIPT_DIR = Path(__file__).parent
INPUT_FILE = SCRIPT_DIR / "scraped_data" / "complete_capture.json"
OUTPUT_FILE = SCRIPT_DIR / "scraped_data" / "goodshort_production_data.json"

def extract_book_id_from_url(url):
    """Extract book ID from video URL"""
    # URL format: .../books/502/31000991502/469570/...
    parts = url.split('/books/')
    if len(parts) > 1:
        segments = parts[1].split('/')
        if len(segments) >= 2:
            return segments[1]  # 31000991502
    return None

def extract_chapter_id_from_url(url):
    """Extract chapter ID from video URL"""
    parts = url.split('/books/')
    if len(parts) > 1:
        segments = parts[1].split('/')
        if len(segments) >= 3:
            return segments[2]  # 469570
    return None

def convert_to_production_format():
    """Convert complete_capture.json to production format"""
    
    print("📂 Loading complete_capture.json...")
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    video_urls = data.get('videoUrls', [])
    print(f"✅ Found {len(video_urls)} video URLs")
    
    # Group by book ID
    dramas_data = defaultdict(lambda: {
        'bookId': '',
        'title': '',
        'description': '',
        'genre': 'Drama',
        'category': 'Drama',
        'author': 'GoodShort',
        'tags': [],
        'totalEpisodes': 0,
        'episodes': [],
        'videoUrls': [],
        'capturedAt': data.get('capturedAt', '')
    })
    
    # Track episodes by book
    episodes_by_book = defaultdict(dict)  # {bookId: {chapterId: {...}}}
    
    # Process video URLs
    for video in video_urls:
        url = video.get('url', '')
        book_id = video.get('bookId') or extract_book_id_from_url(url)
        chapter_id = video.get('chapterId') or extract_chapter_id_from_url(url)
        
        if not book_id:
            continue
        
        drama = dramas_data[book_id]
        drama['bookId'] = book_id
        
        # Add video URL
        if '.m3u8' in url and chapter_id:
            drama['videoUrls'].append({
                'chapterId': chapter_id,
                'url': url.split('?')[0],  # Remove query params
                'resolution': video.get('resolution', '720p'),
                'token': video.get('token', '')
            })
            
            # Create episode entry
            if chapter_id not in episodes_by_book[book_id]:
                episode_num = len(episodes_by_book[book_id]) + 1
                episodes_by_book[book_id][chapter_id] = {
                    'id': chapter_id,
                    'title': f'Episode {episode_num}',
                    'order': episode_num,
                    'isFree': True,
                    'duration': 120
                }
    
    # Convert episodes dict to list
    for book_id in dramas_data:
        if book_id in episodes_by_book:
            episodes = list(episodes_by_book[book_id].values())
            episodes.sort(key=lambda x: x['order'])
            dramas_data[book_id]['episodes'] = episodes
            dramas_data[book_id]['totalEpisodes'] = len(episodes)
            dramas_data[book_id]['title'] = f'Drama {book_id[-6:]}'  # Use last 6 digits
    
    # Create production format
    production_data = {
        'session': {
            'startTime': data.get('capturedAt', ''),
            'version': '5.0-converted',
            'lastUpdate': data.get('capturedAt', '')
        },
        'dramas': dict(dramas_data),
        'covers': {},
        'rawResponses': [],
        'stats': {
            'dramasTotal': len(dramas_data),
            'episodesTotal': sum(len(d['episodes']) for d in dramas_data.values())
        }
    }
    
    # Save
    print(f"\n📊 Converted Data:")
    print(f"  - Dramas: {production_data['stats']['dramasTotal']}")
    print(f"  - Episodes: {production_data['stats']['episodesTotal']}")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(production_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Saved to: {OUTPUT_FILE}")
    
    # Show drama details
    print(f"\n📚 Dramas:")
    for book_id, drama in production_data['dramas'].items():
        print(f"  - {drama['title']} ({len(drama['episodes'])} episodes)")
    
    return OUTPUT_FILE

if __name__ == "__main__":
    convert_to_production_format()
