"""
GoodShort HAR File Analyzer - Fresh Capture
Analyzes fresh_capture.har to extract all drama data
"""

import json
import re
from collections import defaultdict
from urllib.parse import urlparse, parse_qs
from pathlib import Path

# File paths
HAR_FILE = Path("fresh_capture.har")
OUTPUT_DIR = Path("fresh_capture_analysis")
OUTPUT_DIR.mkdir(exist_ok=True)

print("=" * 80)
print("🔍 GOODSHORT HAR ANALYZER - FRESH CAPTURE")
print("=" * 80)

# Load HAR file
print(f"\n📂 Loading HAR file: {HAR_FILE}")
with open(HAR_FILE, 'r', encoding='utf-8') as f:
    har_data = json.load(f)

entries = har_data['log']['entries']
print(f"✅ Loaded {len(entries)} HTTP requests/responses")

# Data containers
dramas = {}
episodes_by_drama = defaultdict(list)
video_segments = defaultdict(list)
cover_images = {}
api_calls = {
    'book_details': [],
    'chapter_list': [],
    'chapter_info': [],
    'video_play': []
}

print("\n" + "=" * 80)
print("📊 ANALYZING REQUESTS...")
print("=" * 80)

# Analyze all entries
for idx, entry in enumerate(entries):
    url = entry['request']['url']
    
    # Parse API calls
    if 'api-akm.goodreels.com' in url or 'api.goodreels.com' in url:
        
        # Book Details (Drama Metadata)
        if '/book/details' in url or '/book/info' in url:
            try:
                response_text = entry['response']['content'].get('text', '')
                if response_text:
                    data = json.loads(response_text)
                    if data.get('code') == 1000 and 'data' in data:
                        book = data['data']
                        book_id = book.get('id')
                        
                        dramas[book_id] = {
                            'id': book_id,
                            'title': book.get('name', 'Unknown'),
                            'description': book.get('introduction', ''),
                            'cover_url': book.get('coverImg', ''),
                            'genre': book.get('genreName', ''),
                            'author': book.get('authorName', ''),
                            'rating': book.get('score', 0),
                            'view_count': book.get('viewCount', 0),
                            'chapter_count': book.get('chapterCount', 0),
                            'status': book.get('status', 0)
                        }
                        api_calls['book_details'].append(data)
                        print(f"  📖 Found Drama: {book.get('name')} (ID: {book_id})")
            except Exception as e:
                pass
        
        # Chapter List (Episodes)
        elif '/book/chapterList' in url or '/chapter/list' in url:
            try:
                response_text = entry['response']['content'].get('text', '')
                if response_text:
                    data = json.loads(response_text)
                    if data.get('code') == 1000 and 'data' in data:
                        chapters = data['data']
                        if isinstance(chapters, list):
                            # Extract book ID from request
                            parsed = urlparse(url)
                            params = parse_qs(parsed.query)
                            book_id = params.get('bookId', [None])[0] or params.get('id', [None])[0]
                            
                            if book_id:
                                for chapter in chapters:
                                    episode_data = {
                                        'id': chapter.get('id'),
                                        'title': chapter.get('name', chapter.get('title', f"Episode {chapter.get('sequence', 0)}")),
                                        'sequence': chapter.get('sequence', 0),
                                        'book_id': book_id,
                                        'duration': chapter.get('duration', 0),
                                        'cover': chapter.get('coverImg', '')
                                    }
                                    episodes_by_drama[book_id].append(episode_data)
                                
                                api_calls['chapter_list'].append(data)
                                print(f"  📺 Found {len(chapters)} episodes for Drama ID: {book_id}")
            except Exception as e:
                pass
        
        # Chapter Info (Individual Episode)
        elif '/chapter/info' in url:
            try:
                response_text = entry['response']['content'].get('text', '')
                if response_text:
                    data = json.loads(response_text)
                    api_calls['chapter_info'].append(data)
            except Exception as e:
                pass
        
        # Video Play Info
        elif '/videobook/play' in url or '/video/play' in url:
            try:
                response_text = entry['response']['content'].get('text', '')
                if response_text:
                    data = json.loads(response_text)
                    api_calls['video_play'].append(data)
            except Exception as e:
                pass
    
    # Parse Video Segments (.ts files)
    if url.endswith('.ts') and ('goodreels.com' in url or 'v2-akm.goodreels.com' in url):
        # Extract book ID and episode info from URL pattern
        # Pattern: /mts/books/{book_id}/{episode_id}/{quality}/{segment}.ts
        match = re.search(r'/books/(\d+)/(\d+)/', url)
        if match:
            book_id = match.group(1)
            episode_id = match.group(2)
            
            video_segments[f"{book_id}_{episode_id}"].append(url)
    
    # Parse Cover Images
    if ('.jpg' in url or '.png' in url) and ('goodreels.com' in url):
        if '/videobook/' in url or '/cover' in url.lower():
            # Try to extract book ID
            match = re.search(r'/videobook/(\d+)/', url)
            if match:
                book_id = match.group(1)
                if book_id not in cover_images:
                    cover_images[book_id] = url

# Sort episodes by sequence
for book_id in episodes_by_drama:
    episodes_by_drama[book_id].sort(key=lambda x: x['sequence'])

print("\n" + "=" * 80)
print("📊 ANALYSIS SUMMARY")
print("=" * 80)

print(f"\n🎬 DRAMAS FOUND: {len(dramas)}")
for book_id, drama in dramas.items():
    print(f"  • {drama['title']}")
    print(f"    - ID: {book_id}")
    print(f"    - Genre: {drama['genre']}")
    print(f"    - Episodes: {drama['chapter_count']}")
    print(f"    - Rating: {drama['rating']}")
    print(f"    - Views: {drama['view_count']:,}")

print(f"\n📺 EPISODES FOUND: {sum(len(eps) for eps in episodes_by_drama.values())} total")
for book_id, episodes in episodes_by_drama.items():
    drama_title = dramas.get(int(book_id), {}).get('title', f'Drama ID {book_id}')
    print(f"  • {drama_title}: {len(episodes)} episodes")

print(f"\n🎥 VIDEO SEGMENTS FOUND: {sum(len(segs) for segs in video_segments.values())} total")
unique_videos = len(video_segments)
print(f"  • Unique episode videos: {unique_videos}")

print(f"\n🖼️ COVER IMAGES FOUND: {len(cover_images)}")

print(f"\n📡 API CALLS CAPTURED:")
print(f"  • Book Details: {len(api_calls['book_details'])}")
print(f"  • Chapter Lists: {len(api_calls['chapter_list'])}")
print(f"  • Chapter Info: {len(api_calls['chapter_info'])}")
print(f"  • Video Play: {len(api_calls['video_play'])}")

# Save detailed analysis
print("\n" + "=" * 80)
print("💾 SAVING ANALYSIS RESULTS...")
print("=" * 80)

# 1. Save dramas metadata
dramas_file = OUTPUT_DIR / "dramas_metadata.json"
with open(dramas_file, 'w', encoding='utf-8') as f:
    json.dump(dramas, f, indent=2, ensure_ascii=False)
print(f"✅ Saved: {dramas_file}")

# 2. Save episodes
episodes_file = OUTPUT_DIR / "episodes_by_drama.json"
with open(episodes_file, 'w', encoding='utf-8') as f:
    json.dump(dict(episodes_by_drama), f, indent=2, ensure_ascii=False)
print(f"✅ Saved: {episodes_file}")

# 3. Save video segments
segments_file = OUTPUT_DIR / "video_segments.json"
with open(segments_file, 'w', encoding='utf-8') as f:
    json.dump(dict(video_segments), f, indent=2, ensure_ascii=False)
print(f"✅ Saved: {segments_file}")

# 4. Save cover images
covers_file = OUTPUT_DIR / "cover_images.json"
with open(covers_file, 'w', encoding='utf-8') as f:
    json.dump(cover_images, f, indent=2, ensure_ascii=False)
print(f"✅ Saved: {covers_file}")

# 5. Save API calls
api_file = OUTPUT_DIR / "api_calls.json"
with open(api_file, 'w', encoding='utf-8') as f:
    json.dump(api_calls, f, indent=2, ensure_ascii=False)
print(f"✅ Saved: {api_file}")

# Generate detailed report
print("\n" + "=" * 80)
print("📝 GENERATING DETAILED REPORT...")
print("=" * 80)

report_lines = []
report_lines.append("# GoodShort Fresh Capture Analysis Report")
report_lines.append(f"\n**Generated:** {Path(HAR_FILE).stat().st_mtime}")
report_lines.append(f"**HAR File Size:** {Path(HAR_FILE).stat().st_size / (1024*1024):.2f} MB")
report_lines.append(f"**Total Requests:** {len(entries)}")

report_lines.append("\n## 🎬 Dramas Captured\n")
for book_id, drama in dramas.items():
    report_lines.append(f"### Drama: {drama['title']}")
    report_lines.append(f"- **ID:** {book_id}")
    report_lines.append(f"- **Genre:** {drama['genre']}")
    report_lines.append(f"- **Author:** {drama['author']}")
    report_lines.append(f"- **Rating:** {drama['rating']}/10")
    report_lines.append(f"- **Views:** {drama['view_count']:,}")
    report_lines.append(f"- **Total Episodes:** {drama['chapter_count']}")
    report_lines.append(f"- **Status:** {drama['status']}")
    report_lines.append(f"- **Cover URL:** {drama['cover_url']}")
    report_lines.append(f"- **Description:** {drama['description'][:200]}...")
    report_lines.append("")

report_lines.append("\n## 📺 Episodes Breakdown\n")
for book_id, episodes in episodes_by_drama.items():
    drama_title = dramas.get(int(book_id), {}).get('title', f'Drama ID {book_id}')
    report_lines.append(f"### {drama_title} ({len(episodes)} episodes)\n")
    for ep in episodes[:5]:  # Show first 5
        report_lines.append(f"- Episode {ep['sequence']}: {ep['title']} (ID: {ep['id']})")
    if len(episodes) > 5:
        report_lines.append(f"- ... and {len(episodes) - 5} more episodes")
    report_lines.append("")

report_lines.append("\n## 🎥 Video Segments Sample\n")
for key, segments in list(video_segments.items())[:3]:
    report_lines.append(f"### Video: {key}")
    report_lines.append(f"- Total segments: {len(segments)}")
    report_lines.append(f"- Sample URL: {segments[0]}")
    report_lines.append("")

report_file = OUTPUT_DIR / "analysis_report.md"
with open(report_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(report_lines))
print(f"✅ Saved: {report_file}")

# Final summary
print("\n" + "=" * 80)
print("✅ ANALYSIS COMPLETE!")
print("=" * 80)
print(f"\n📁 All results saved to: {OUTPUT_DIR}/")
print("\nNext steps:")
print("  1. Download cover images")
print("  2. Download video segments")
print("  3. Combine videos to MP4")
print("  4. Organize to r2_ready structure")
print("  5. Upload to R2")
print("\n" + "=" * 80)
