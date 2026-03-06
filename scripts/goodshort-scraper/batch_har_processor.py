#!/usr/bin/env python3
"""
BATCH HAR PROCESSOR - Scale GoodShort Scraping
==============================================

Process multiple HAR files in batch to extract drama metadata and download videos.

Features:
- Process multiple HAR files in sequence
- Extract all dramas from each HAR
- Deduplicate by BookID across batches
- Parallel video segment downloads
- Resume capability (skip already processed dramas)
- Progress tracking and reporting

Usage:
    python batch_har_processor.py --har-dir ./har_files/ --output ./r2_ready/
    python batch_har_processor.py --har-file batch_01.har --output ./r2_ready/
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from collections import defaultdict
import time
from datetime import datetime

# Configuration
MAX_PARALLEL_DOWNLOADS = 5  # Concurrent segment downloads
REQUEST_TIMEOUT = 30  # Seconds
RETRY_ATTEMPTS = 3
RETRY_DELAY = 2  # Seconds

class BatchHARProcessor:
    """Process multiple HAR files to extract GoodShort dramas"""
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # Tracking
        self.processed_book_ids: Set[str] = set()
        self.processed_dramas: List[str] = []
        self.failed_dramas: List[Dict] = []
        self.skipped_dramas: List[str] = []
        
        # Load already processed dramas
        self._load_processed_dramas()
    
    def _load_processed_dramas(self):
        """Load BookIDs of already processed dramas to prevent duplicates"""
        for folder in self.output_dir.iterdir():
            if not folder.is_dir():
                continue
            
            metadata_file = folder / "metadata.json"
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        book_id = metadata.get('bookId')
                        if book_id:
                            self.processed_book_ids.add(str(book_id))
                except Exception as e:
                    print(f"⚠️  Could not load metadata from {folder.name}: {e}")
        
        print(f"📊 Loaded {len(self.processed_book_ids)} already processed dramas\n")
    
    def extract_dramas_from_har(self, har_file: Path) -> List[Dict]:
        """Extract all drama metadata from HAR file"""
        print(f"\n{'='*70}")
        print(f"📁 Processing HAR: {har_file.name}")
        print(f"{'='*70}\n")
        
        with open(har_file, 'r', encoding='utf-8') as f:
            har_data = json.load(f)
        
        dramas = []
        drama_map = {}  # book_id -> drama_data
        
        # STEP 1: Extract book metadata from /book/quick/open, /book/foru/introduction
        print("Step 1: Extracting book metadata...")
        for entry in har_data['log']['entries']:
            request_url = entry['request']['url']
            
            if '/hwycclientreels/book/' in request_url and ('quick/open' in request_url or 'foru/introduction' in request_url):
                response = entry.get('response', {})
                content = response.get('content', {})
                text = content.get('text', '')
                
                if not text:
                    continue
                
                try:
                    data = json.loads(text)
                    book_data = data.get('data', {})
                    
                    # Extract book info
                    book = book_data.get('book', book_data.get('info', book_data))
                    if not isinstance(book, dict):
                        continue
                    
                    book_id = str(book.get('bookId', book.get('id', '')))
                    name = book.get('name', book.get('bookName', book.get('title', '')))
                    
                    if not book_id or not name:
                        continue
                    
                    # Skip if already processed
                    if book_id in self.processed_book_ids:
                        print(f"  ⏭️  Skipping {name} (already processed)")
                        continue
                    
                    drama_map[book_id] = {
                        'bookId': book_id,
                        'title': name,
                        'description': book.get('description', book.get('desc', '')),
                        'cover': book.get('largeCover', book.get('cover', '')),
                        'total_episodes': book.get('chapterCount', book.get('sections', 0)),
                        'episodes': []
                    }
                    
                    print(f"  ✅ Found: {name} (ID: {book_id})")
                
                except json.JSONDecodeError:
                    continue
        
        print(f"\n  Found {len(drama_map)} unique dramas\n")
        
        # STEP 2: Extract episodes from /chapter/list
        print("Step 2: Extracting episode data...")
        for entry in har_data['log']['entries']:
            request_url = entry['request']['url']
            
            if '/hwycclientreels/chapter/list' in request_url:
                response = entry.get('response', {})
                content = response.get('content', {})
                text = content.get('text', '')
                
                if not text:
                    continue
                
                try:
                    data = json.loads(text)
                    chapters = data.get('data', {}).get('list', [])
                    
                    if not chapters:
                        continue
                    
                    # Group chapters by bookId
                    for chapter in chapters:
                        if not isinstance(chapter, dict):
                            continue
                        
                        book_id = str(chapter.get('bookId', ''))
                        if not book_id or book_id not in drama_map:
                            continue
                        
                        # Extract episode data
                        episode_data = {
                            'index': chapter.get('index', chapter.get('sectionIndex', 0)),
                            'chapterId': chapter.get('id', chapter.get('chapterId', '')),
                            'chapterName': chapter.get('chapterName', chapter.get('name', '')),
                            'playTime': chapter.get('playTime', chapter.get('duration', 0)),
                            'video_url': chapter.get('videoUrl', chapter.get('videoLink', '')),
                            'cover': chapter.get('largeCover', chapter.get('cover', chapter.get('image', '')))
                        }
                        
                        # Avoid duplicates
                        chapter_id = str(episode_data['chapterId'])
                        existing_ids = [str(ep.get('chapterId')) for ep in drama_map[book_id]['episodes']]
                        if chapter_id not in existing_ids:
                            drama_map[book_id]['episodes'].append(episode_data)
                
                except json.JSONDecodeError:
                    continue
        
        # Update episode counts
        for book_id, drama in drama_map.items():
            actual_count = len(drama['episodes'])
            print(f"  {drama['title']}: {actual_count} episodes")
            if actual_count > 0:
                drama['total_episodes'] = actual_count
        
        # Convert to list
        dramas = list(drama_map.values())
        
        print(f"\n📊 Extracted {len(dramas)} dramas from {har_file.name}")
        return dramas
    
    def sanitize_filename(self, title: str) -> str:
        """Convert title to safe folder name"""
        # Remove/replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            title = title.replace(char, '_')
        
        # Replace spaces and multiple underscores
        title = '_'.join(title.split())
        title = '_'.join(filter(None, title.split('_')))
        
        return title[:100]  # Limit length
    
    def download_file(self, url: str, output_path: Path, retry=RETRY_ATTEMPTS) -> bool:
        """Download single file with retry logic"""
        for attempt in range(retry):
            try:
                response = requests.get(url, timeout=REQUEST_TIMEOUT, stream=True)
                response.raise_for_status()
                
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                return True
            
            except Exception as e:
                if attempt < retry - 1:
                    time.sleep(RETRY_DELAY)
                    continue
                else:
                    print(f"      ❌ Failed to download {output_path.name}: {e}")
                    return False
        
        return False
    
    def download_episode_parallel(self, episode_data: Dict, drama_folder: Path, episode_index: int) -> bool:
        """Download single episode's video URL and parse M3U8"""
        video_url = episode_data.get('video_url', '')
        if not video_url:
            return False
        
        episode_folder = drama_folder / f"episode_{episode_index:03d}"
        episode_folder.mkdir(parents=True, exist_ok=True)
        
        print(f"    📥 Episode {episode_index + 1}...")
        
        # Download M3U8 playlist
        try:
            response = requests.get(video_url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            m3u8_content = response.text
            
            # Parse M3U8 to get segment URLs
            base_url = '/'.join(video_url.split('/')[:-1])
            segment_urls = []
            
            for line in m3u8_content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    # Relative or absolute URL
                    if line.startswith('http'):
                        segment_urls.append(line)
                    else:
                        segment_urls.append(f"{base_url}/{line}")
            
            print(f"      Found {len(segment_urls)} segments")
            
            # Download segments in parallel
            with ThreadPoolExecutor(max_workers=MAX_PARALLEL_DOWNLOADS) as executor:
                futures = {}
                
                for i, segment_url in enumerate(segment_urls):
                    segment_name = segment_url.split('/')[-1]
                    segment_path = episode_folder / segment_name
                    
                    future = executor.submit(self.download_file, segment_url, segment_path)
                    futures[future] = segment_name
                
                # Wait for completion
                completed = 0
                for future in as_completed(futures):
                    if future.result():
                        completed += 1
            
            # Save playlist
            playlist_path = episode_folder / "playlist.m3u8"
            # Rewrite M3U8 with local segment names
            local_m3u8 = []
            for line in m3u8_content.split('\n'):
                if line.strip() and not line.startswith('#'):
                    segment_name = line.strip().split('/')[-1]
                    local_m3u8.append(segment_name)
                else:
                    local_m3u8.append(line)
            
            with open(playlist_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(local_m3u8))
            
            print(f"      ✅ Downloaded {completed}/{len(segment_urls)} segments")
            return completed == len(segment_urls)
        
        except Exception as e:
            print(f"      ❌ Failed: {e}")
            return False
    
    def process_drama(self, drama_data: Dict) -> bool:
        """Process single drama: download cover, videos, save metadata"""
        book_id = drama_data['bookId']
        title = drama_data['title']
        
        # Skip if already processed
        if book_id in self.processed_book_ids:
            self.skipped_dramas.append(title)
            return False
        
        print(f"\n{'='*70}")
        print(f"🎬 Processing: {title}")
        print(f"   BookID: {book_id}")
        print(f"   Episodes: {len(drama_data['episodes'])}")
        print(f"{'='*70}\n")
        
        # Create drama folder
        folder_name = self.sanitize_filename(title)
        drama_folder = self.output_dir / folder_name
        drama_folder.mkdir(parents=True, exist_ok=True)
        
        try:
            # Download cover
            cover_url = drama_data.get('cover', '')
            if cover_url:
                cover_path = drama_folder / "cover.jpg"
                print(f"  📷 Downloading cover...")
                self.download_file(cover_url, cover_path)
            
            # Download episodes
            successful_episodes = 0
            for ep in drama_data['episodes']:
                episode_index = ep.get('index', 0)
                
                if self.download_episode_parallel(ep, drama_folder, episode_index):
                    successful_episodes += 1
            
            # Save metadata
            metadata_path = drama_folder / "metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(drama_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n  ✅ Completed: {successful_episodes}/{len(drama_data['episodes'])} episodes")
            
            # Mark as processed
            self.processed_book_ids.add(book_id)
            self.processed_dramas.append(title)
            
            return True
        
        except Exception as e:
            print(f"\n  ❌ Failed to process {title}: {e}")
            self.failed_dramas.append({'title': title, 'error': str(e)})
            return False
    
    def process_har_file(self, har_file: Path):
        """Process single HAR file"""
        dramas = self.extract_dramas_from_har(har_file)
        
        for drama in dramas:
            self.process_drama(drama)
    
    def process_batch(self, har_files: List[Path]):
        """Process multiple HAR files"""
        print(f"\n{'='*70}")
        print(f"🚀 BATCH HAR PROCESSOR")
        print(f"{'='*70}")
        print(f"HAR files: {len(har_files)}")
        print(f"Output directory: {self.output_dir}")
        print(f"{'='*70}\n")
        
        start_time = time.time()
        
        for har_file in har_files:
            self.process_har_file(har_file)
        
        elapsed = time.time() - start_time
        
        # Final report
        self.print_summary(elapsed)
    
    def print_summary(self, elapsed_time: float):
        """Print processing summary"""
        print(f"\n{'='*70}")
        print(f"📊 BATCH PROCESSING COMPLETE")
        print(f"{'='*70}\n")
        
        print(f"⏱️  Time elapsed: {elapsed_time/60:.1f} minutes\n")
        
        print(f"✅ Successfully processed: {len(self.processed_dramas)}")
        if self.processed_dramas:
            for drama in self.processed_dramas:
                print(f"   - {drama}")
        
        if self.skipped_dramas:
            print(f"\n⏭️  Skipped (already processed): {len(self.skipped_dramas)}")
            for drama in self.skipped_dramas:
                print(f"   - {drama}")
        
        if self.failed_dramas:
            print(f"\n❌ Failed: {len(self.failed_dramas)}")
            for failure in self.failed_dramas:
                print(f"   - {failure['title']}: {failure['error']}")
        
        print(f"\n📁 Output directory: {self.output_dir}")
        print(f"   Total dramas: {len(list(self.output_dir.iterdir()))}")
        
        print(f"\n{'='*70}\n")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Batch process GoodShort HAR files')
    parser.add_argument('--har-dir', type=str, help='Directory containing HAR files')
    parser.add_argument('--har-file', type=str, help='Single HAR file to process')
    parser.add_argument('--output', type=str, default='./r2_ready', help='Output directory')
    
    args = parser.parse_args()
    
    output_dir = Path(args.output)
    
    # Collect HAR files
    har_files = []
    
    if args.har_file:
        har_files.append(Path(args.har_file))
    elif args.har_dir:
        har_dir = Path(args.har_dir)
        har_files = sorted(har_dir.glob('*.har'))
    else:
        print("❌ Please specify --har-dir or --har-file")
        sys.exit(1)
    
    if not har_files:
        print("❌ No HAR files found")
        sys.exit(1)
    
    # Process
    processor = BatchHARProcessor(output_dir)
    processor.process_batch(har_files)


if __name__ == "__main__":
    main()
