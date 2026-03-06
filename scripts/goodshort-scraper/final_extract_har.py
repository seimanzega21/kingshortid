"""
FINAL HAR Extractor - Correct Parsing Logic
Extracts all drama, episode, and media data from fresh_capture.har
"""

import json
import sys
import io
import re
from pathlib import Path
from collections import defaultdict
from urllib.parse import urlparse, parse_qs

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HAR_FILE = Path("fresh_capture.har")
OUTPUT_DIR = Path("extracted_data")
OUTPUT_DIR.mkdir(exist_ok=True)

print("=" * 70)
print("FINAL HAR EXTRACTOR - GOODSHORT CAPTURE")
print("=" * 70)

# Load HAR
with open(HAR_FILE, 'r', encoding='utf-8') as f:
    har_data = json.load(f)

entries = har_data['log']['entries']
print(f"\nTotal Requests: {len(entries)}")

# Data containers
dramas = {}
episodes_by_book = defaultdict(list)
video_segments = defaultdict(list)
cover_images = {}

# Extract data
for entry in entries:
    url = entry['request']['url']
    
    # =======================================================================
    # 1. EXTRACT DRAMA METADATA
    # =======================================================================
    if 'api-akm.goodreels.com' in url or 'api.goodreels.com' in url:
        try:
            response_text = entry['response']['content'].get('text', '')
            if not response_text or len(response_text) < 20:
                continue
                
            data = json.loads(response_text)
            
            # Check for nested book object
            if 'data' in data and isinstance(data['data'], dict):
                datum = data['data']
                
                # Pattern 1: data.book.bookName
                if 'book' in datum and isinstance(datum['book'], dict):
                    book = datum['book']
                    book_id = book.get('bookId')
                    
                    if book_id and book.get('bookName'):
                        dramas[book_id] = {
                            'id': book_id,
                            'title': book.get('bookName'),
                            'author': book.get('pseudonym', book.get('producer', '')),
                            'description': book.get('introduction', ''),
                            'cover_url': book.get('cover', ''),
                            'genre': '',  # Will try to get from other fields
                            'chapter_count': book.get('chapterCount', 0),
                            'view_count': book.get('viewCount', 0),
                            'rating': book.get('ratings', 0),
                            'language': book.get('languageDisplay', 'Bahasa Indonesia')
                        }
                        print(f"  Found Drama: {book.get('bookName')} (ID: {book_id})")
                
                # Pattern 2: List of chapters/episodes
                if 'chapters' in datum and isinstance(datum['chapters'], list):
                    for chapter in datum['chapters']:
                        episodes_by_book[chapter.get('bookId', 'unknown')].append(chapter)
                
                # Pattern 3: Single chapter info
                if 'chapter' in datum and isinstance(datum['chapter'], dict):
                    ch = datum['chapter']
                    episodes_by_book[ch.get('bookId', 'unknown')].append(ch)
        
        except Exception as e:
            continue
    
    # =======================================================================
    # 2. EXTRACT VIDEO SEGMENTS
    # =======================================================================
    if url.endswith('.ts') and 'goodreels.com' in url:
        # Pattern: /mts/books/{book_id}/{episode_id}/...
        match = re.search(r'/books/(\d+)/(\d+)/', url)
        if match:
            book_id = match.group(1)
            episode_id = match.group(2)
            key = f"{book_id}_{episode_id}"
            video_segments[key].append(url)
    
    # =======================================================================
    # 3. EXTRACT COVER IMAGES
    # =======================================================================
    if ('.jpg' in url or '.png' in url or '.webp' in url) and 'goodreels.com' in url:
        if '/videobook/' in url:
            # Try to extract book ID from URL
            match = re.search(r'/videobook/(\d+)/', url)
            if match:
                book_id = match.group(1)
                if book_id not in cover_images:
                    cover_images[book_id] = url

print("\n" + "=" * 70)
print("EXTRACTION RESULTS")
print("=" * 70)

print(f"\nDramas: {len(dramas)}")
for book_id, drama in dramas.items():
    print(f"  - {drama['title']} ({drama['chapter_count']} eps)")

print(f"\nEpisodes: {sum(len(eps) for eps in episodes_by_book.values())}")
for book_id, episodes in episodes_by_book.items():
    print(f"  - Book {book_id}: {len(episodes)} episodes")

print(f"\nVideo Segments: {sum(len(segs) for segs in video_segments.values())}")
unique_videos = len(video_segments)
print(f"  - Unique videos: {unique_videos}")

print(f"\nCover Images: {len(cover_images)}")

# Save extracted data
print("\n" + "=" * 70)
print("SAVING EXTRACTED DATA")
print("=" * 70)

# 1. Save dramas
dramas_file = OUTPUT_DIR / "dramas.json"
with open(dramas_file, 'w', encoding='utf-8') as f:
    json.dump(dramas, f, indent=2, ensure_ascii=False)
print(f"Saved: {dramas_file}")

# 2. Save episodes
episodes_file = OUTPUT_DIR / "episodes.json"
with open(episodes_file, 'w', encoding='utf-8') as f:
    json.dump(dict(episodes_by_book), f, indent=2, ensure_ascii=False)
print(f"Saved: {episodes_file}")

# 3. Save video segments
segments_file = OUTPUT_DIR / "video_segments.json"
with open(segments_file, 'w', encoding='utf-8') as f:
    json.dump(dict(video_segments), f, indent=2, ensure_ascii=False)
print(f"Saved: {segments_file}")

# 4. Save cover images
covers_file = OUTPUT_DIR / "covers.json"
with open(covers_file, 'w', encoding='utf-8') as f:
    json.dump(cover_images, f, indent=2, ensure_ascii=False)
print(f"Saved: {covers_file}")

# Generate summary report
summary_lines = []
summary_lines.append("# HAR Extraction Summary\n")
summary_lines.append(f"**Total Requests:** {len(entries)}")
summary_lines.append(f"**Dramas Found:** {len(dramas)}")
summary_lines.append(f"**Episodes Found:** {sum(len(eps) for eps in episodes_by_book.values())}")
summary_lines.append(f"**Video Segments:** {sum(len(segs) for segs in video_segments.values())}")
summary_lines.append(f"**Cover Images:** {len(cover_images)}\n")

summary_lines.append("## Dramas\n")
for book_id, drama in dramas.items():
    summary_lines.append(f"### {drama['title']}")
    summary_lines.append(f"- ID: {book_id}")
    summary_lines.append(f"- Author: {drama['author']}")
    summary_lines.append(f"- Episodes: {drama['chapter_count']}")
    summary_lines.append(f"- Views: {drama['view_count']:,}")
    summary_lines.append(f"- Rating: {drama['rating']}/10")
    summary_lines.append(f"- Cover: {drama['cover_url']}")
    summary_lines.append(f"- Description: {drama['description'][:150]} ...\n")

summary_file = OUTPUT_DIR / "extraction_summary.md"
with open(summary_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(summary_lines))
print(f"Saved: {summary_file}")

print("\n" + "=" * 70)
print("EXTRACTION COMPLETE!")
print("=" * 70)
print(f"\nAll data saved to: {OUTPUT_DIR}/")
