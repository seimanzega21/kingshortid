"""
Full Video Download Pipeline
Downloads all captured video segments organized by book/chapter
"""
import json
import re
import requests
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import time

class VideoDownloader:
    def __init__(self, output_dir='scraped_data/videos'):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.stats = {'success': 0, 'failed': 0, 'skipped': 0}
        
    def parse_url(self, url):
        """Parse video URL to extract metadata"""
        pattern = r'/mts/books/\d+/(\d+)/(\d+)/([^/]+)/(\d+p)/([^/\.]+)'
        match = re.search(pattern, url)
        if match:
            return {
                'book_id': match.group(1),
                'chapter_id': match.group(2),
                'token': match.group(3),
                'resolution': match.group(4),
                'filename': match.group(5)
            }
        return None
    
    def download_segment(self, url, filepath):
        """Download a single video segment"""
        if filepath.exists():
            return 'skipped'
        
        try:
            response = requests.get(url, timeout=60, stream=True)
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return 'success'
            else:
                return 'failed'
        except Exception as e:
            return 'failed'
    
    def download_chapter(self, book_id, chapter_id, segments):
        """Download all segments for a chapter"""
        chapter_dir = self.output_dir / book_id / chapter_id
        chapter_dir.mkdir(parents=True, exist_ok=True)
        
        results = {'success': 0, 'failed': 0, 'skipped': 0}
        
        for i, seg in enumerate(segments):
            url = seg['url']
            filename = f"{seg['filename']}.ts"
            filepath = chapter_dir / filename
            
            result = self.download_segment(url, filepath)
            results[result] += 1
            
            # Progress
            if (i + 1) % 5 == 0:
                print(f"      Progress: {i+1}/{len(segments)}")
        
        return results
    
    def download_all(self, videos_data, max_chapters=None):
        """Download all videos organized by book/chapter"""
        total_chapters = sum(len(c) for c in videos_data.values())
        print(f"\n[*] Starting download: {len(videos_data)} books, {total_chapters} chapters")
        
        chapter_count = 0
        
        for book_id, chapters in videos_data.items():
            print(f"\n[Book {book_id}]")
            
            for chapter_id, segments in chapters.items():
                if max_chapters and chapter_count >= max_chapters:
                    print(f"\n[!] Reached max chapters limit: {max_chapters}")
                    return self.stats
                
                print(f"  [Chapter {chapter_id}] - {len(segments)} segments")
                results = self.download_chapter(book_id, chapter_id, segments)
                
                self.stats['success'] += results['success']
                self.stats['failed'] += results['failed']
                self.stats['skipped'] += results['skipped']
                
                print(f"    OK: {results['success']}, Failed: {results['failed']}, Skipped: {results['skipped']}")
                
                chapter_count += 1
        
        return self.stats

def main():
    print("=" * 60)
    print("VIDEO DOWNLOAD PIPELINE")
    print("=" * 60)
    
    # Load parsed data
    with open('scraped_data/parsed/videos_by_book.json', 'r') as f:
        videos = json.load(f)
    
    total_segments = sum(
        len(segs) 
        for chapters in videos.values() 
        for segs in chapters.values()
    )
    
    print(f"\nBooks: {len(videos)}")
    print(f"Total segments: {total_segments}")
    
    # Ask confirmation
    print("\n[!] This will download all video segments.")
    print(f"    Estimated size: ~{total_segments * 0.5:.0f} MB")
    
    # Download
    downloader = VideoDownloader()
    
    # Download all chapters
    print("\n[*] Downloading all chapters...")
    stats = downloader.download_all(videos, max_chapters=None)
    
    print("\n" + "=" * 60)
    print("DOWNLOAD COMPLETE")
    print("=" * 60)
    print(f"Success: {stats['success']}")
    print(f"Failed: {stats['failed']}")
    print(f"Skipped: {stats['skipped']}")
    print(f"\nFiles saved to: {downloader.output_dir}")

if __name__ == '__main__':
    main()
