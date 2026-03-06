#!/usr/bin/env python3
"""
COMPLETE HAR PROCESSOR - Extract ALL GoodShort Data
====================================================

Extracts COMPLETE data from HAR files:
✅ Book metadata (from /book/quick/open)
✅ Episode lists (from /chapter/list)  
✅ Video URLs (from /chapter/load) ⭐ CRITICAL
✅ Cover images
✅ Complete validation and reporting

Usage:
    python complete_har_processor.py batch_02.har
    python complete_har_processor.py --har-dir ./har_files/
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List
from collections import defaultdict
from datetime import datetime

class CompleteHARProcessor:
    """Extract complete drama data from HAR files"""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("extracted_data")
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # Statistics
        self.stats = {
            'dramas_found': 0,
            'episodes_found': 0,
            'video_urls_found': 0,
            'covers_found': 0
        }
    
    def process_har(self, har_file: Path) -> List[Dict]:
        """Extract ALL data from HAR file"""
        print(f"\n{'='*70}")
        print(f"📁 Processing: {har_file.name}")
        print(f"{'='*70}\n")
        
        with open(har_file, 'r', encoding='utf-8') as f:
            har_data = json.load(f)
        
        dramas = {}  # book_id -> drama_data
        
        # STEP 1: Extract Book Metadata
        print("Step 1/4: Extracting book metadata...")
        self._extract_book_metadata(har_data, dramas)
        
        # STEP 2: Extract Episode Lists
        print("\nStep 2/4: Extracting episode lists...")
        self._extract_episodes(har_data, dramas)
        
        # STEP 3: Extract Video URLs ⭐ CRITICAL!
        print("\nStep 3/4: Extracting video URLs from /chapter/load...")
        self._extract_video_urls(har_data, dramas)
        
        # STEP 4: Extract Covers
        print("\nStep 4/4: Extracting cover URLs...")
        self._extract_covers(har_data, dramas)
        
        # Convert to list
        drama_list = list(dramas.values())
        
        # Print results
        self._print_results(drama_list)
        
        # Save to JSON
        self._save_results(drama_list, har_file.stem)
        
        return drama_list
    
    def _extract_book_metadata(self, har_data: Dict, dramas: Dict):
        """Extract book metadata from /book/quick/open"""
        for entry in har_data['log']['entries']:
            url = entry['request']['url']
            
            if '/hwycclientreels/book/' not in url:
                continue
            if 'quick/open' not in url and 'foru/introduction' not in url:
                continue
            
            response = entry.get('response', {})
            content = response.get('content', {})
            text = content.get('text', '')
            
            if not text:
                continue
            
            try:
                data = json.loads(text)
                book_data = data.get('data', {})
                book = book_data.get('book', book_data.get('info', book_data))
                
                if not isinstance(book, dict):
                    continue
                
                book_id = str(book.get('bookId', book.get('id', '')))
                name = book.get('name', book.get('bookName', book.get('title', '')))
                
                if not book_id or not name:
                    continue
                
                dramas[book_id] = {
                    'bookId': book_id,
                    'title': name,
                    'description': book.get('description', book.get('desc', '')),
                    'coverUrl': book.get('largeCover', book.get('cover', '')),
                    'totalEpisodes': book.get('chapterCount', book.get('sections', 0)),
                    'tags': book.get('tags', []),
                    'score': book.get('score', 0),
                    'episodes': []
                }
                
                self.stats['dramas_found'] += 1
                print(f"  ✅ {name} (ID: {book_id})")
            
            except json.JSONDecodeError:
                continue
        
        print(f"\n  Found {len(dramas)} dramas")
    
    def _extract_episodes(self, har_data: Dict, dramas: Dict):
        """Extract episode lists from /chapter/list"""
        for entry in har_data['log']['entries']:
            url = entry['request']['url']
            
            if '/hwycclientreels/chapter/list' not in url:
                continue
            
            response = entry.get('response', {})
            content = response.get('content', {})
            text = content.get('text', '')
            
            if not text:
                continue
            
            try:
                data = json.loads(text)
                chapters = data.get('data', {}).get('list', [])
                
                for chapter in chapters:
                    if not isinstance(chapter, dict):
                        continue
                    
                    book_id = str(chapter.get('bookId', ''))
                    if book_id not in dramas:
                        continue
                    
                    chapter_id = str(chapter.get('id', chapter.get('chapterId', '')))
                    
                    # Check for duplicates
                    existing_ids = [ep['chapterId'] for ep in dramas[book_id]['episodes']]
                    if chapter_id in existing_ids:
                        continue
                    
                    episode = {
                        'chapterId': chapter_id,
                        'index': chapter.get('index', chapter.get('sectionIndex', 0)),
                        'name': chapter.get('chapterName', chapter.get('name', '')),
                        'duration': chapter.get('playTime', chapter.get('duration', 0)),
                        'videoUrl': None,  # Will be filled in step 3
                        'cover': chapter.get('largeCover', chapter.get('cover', ''))
                    }
                    
                    dramas[book_id]['episodes'].append(episode)
                    self.stats['episodes_found'] += 1
            
            except json.JSONDecodeError:
                continue
        
        # Update actual episode counts
        for drama in dramas.values():
            if dramas[drama['bookId']]['episodes']:
                drama['totalEpisodes'] = len(drama['episodes'])
                print(f"  {drama['title']}: {drama['totalEpisodes']} episodes")
    
    def _extract_video_urls(self, har_data: Dict, dramas: Dict):
        """Extract video URLs from /chapter/load ⭐ CRITICAL"""
        video_count = 0
        
        for entry in har_data['log']['entries']:
            url = entry['request']['url']
            
            if '/hwycclientreels/chapter/load' not in url:
                continue
            
            response = entry.get('response', {})
            content = response.get('content', {})
            text = content.get('text', '')
            
            if not text:
                continue
            
            try:
                data = json.loads(text)
                chapter_data = data.get('data', {})
                
                # Extract video URL
                video_url = chapter_data.get('videoUrl')
                if not video_url:
                    # Try alternative paths
                    video = chapter_data.get('video', {})
                    video_url = video.get('url', video.get('videoUrl', ''))
                
                if not video_url:
                    continue
                
                # Get chapter and book IDs
                chapter_id = str(chapter_data.get('chapterId', chapter_data.get('id', '')))
                book_id = str(chapter_data.get('bookId', ''))
                
                if not chapter_id or book_id not in dramas:
                    continue
                
                # Update episode with video URL
                for episode in dramas[book_id]['episodes']:
                    if episode['chapterId'] == chapter_id:
                        episode['videoUrl'] = video_url
                        video_count += 1
                        self.stats['video_urls_found'] += 1
                        break
            
            except json.JSONDecodeError:
                continue
        
        print(f"  ✅ Added {video_count} video URLs to episodes")
    
    def _extract_covers(self, har_data: Dict, dramas: Dict):
        """Extract cover image URLs from CDN requests"""
        for entry in har_data['log']['entries']:
            url = entry['request']['url']
            
            if 'cdn-hw.video.shortlovers.id' in url and '/videobook/' in url:
                # Extract book ID from URL
                import re
                match = re.search(r'/videobook/(\d+)/', url)
                if match:
                    book_id = match.group(1)
                    if book_id in dramas and not dramas[book_id].get('coverUrl'):
                        dramas[book_id]['coverUrl'] = url.split('?')[0]
                        self.stats['covers_found'] += 1
    
    def _print_results(self, dramas: List[Dict]):
        """Print extraction results"""
        print(f"\n{'='*70}")
        print("📊 EXTRACTION RESULTS")
        print(f"{'='*70}\n")
        
        print(f"✅ Dramas found: {self.stats['dramas_found']}")
        print(f"✅ Episodes found: {self.stats['episodes_found']}")
        print(f"✅ Video URLs found: {self.stats['video_urls_found']}")
        print(f"✅ Covers found: {self.stats['covers_found']}")
        
        print(f"\n{'='*70}")
        print("📋 DRAMA DETAILS")
        print(f"{'='*70}\n")
        
        for drama in dramas:
            episodes_with_videos = sum(1 for ep in drama['episodes'] if ep.get('videoUrl'))
            total_eps = len(drama['episodes'])
            
            print(f"📺 {drama['title']}")
            print(f"   ├─ Episodes: {total_eps}")
            print(f"   ├─ With video URLs: {episodes_with_videos}/{total_eps}")
            print(f"   ├─ Cover: {'✅' if drama.get('coverUrl') else '❌'}")
            print(f"   └─ Description: {len(drama.get('description', ''))} chars\n")
    
    def _save_results(self, dramas: List[Dict], filename_prefix: str):
        """Save extracted data to JSON"""
        output_file = self.output_dir / f"{filename_prefix}_extracted.json"
        
        output_data = {
            'extractedAt': datetime.now().isoformat(),
            'statistics': self.stats,
            'dramas': dramas
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Saved to: {output_file}")
        print(f"   File size: {output_file.stat().st_size:,} bytes\n")
        
        # Also save individual drama files
        for drama in dramas:
            drama_folder = self.output_dir / self._sanitize_filename(drama['title'])
            drama_folder.mkdir(exist_ok=True, parents=True)
            
            drama_file = drama_folder / "metadata.json"
            with open(drama_file, 'w', encoding='utf-8') as f:
                json.dump(drama, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Also saved {len(dramas)} individual drama folders\n")
    
    def _sanitize_filename(self, title: str) -> str:
        """Convert title to safe folder name"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            title = title.replace(char, '_')
        title = '_'.join(title.split())
        return title[:100]

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python complete_har_processor.py <har_file>")
        print("Example: python complete_har_processor.py batch_02.har")
        sys.exit(1)
    
    har_file = Path(sys.argv[1])
    
    if not har_file.exists():
        # Try in har_files directory
        har_file = Path("har_files") / har_file.name
        if not har_file.exists():
            print(f"❌ HAR file not found: {sys.argv[1]}")
            sys.exit(1)
    
    processor = CompleteHARProcessor()
    dramas = processor.process_har(har_file)
    
    print(f"{'='*70}")
    print(f"✅ PROCESSING COMPLETE!")
    print(f"{'='*70}\n")
    print(f"Total dramas extracted: {len(dramas)}")
    print(f"Total episodes: {sum(len(d['episodes']) for d in dramas)}")
    print(f"Total video URLs: {sum(1 for d in dramas for ep in d['episodes'] if ep.get('videoUrl'))}")
    print(f"\nReady for import to database! 🎉\n")

if __name__ == '__main__':
    main()
