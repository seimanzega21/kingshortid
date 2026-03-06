#!/usr/bin/env python3
"""
GoodShort Production Data Processor
====================================

Process captured data from Frida production-scraper.js:
- Load metadata from goodshort_production_data.json
- Download high-quality covers
- Organize episodes in sequential order (1, 2, 3...)
- Generate R2-ready folder structure
- Create comprehensive metadata files

Usage:
    python process_production_capture.py
    python process_production_capture.py --input custom_data.json --output custom_output/
"""

import json
import os
import re
import requests
from pathlib import Path
from typing import Dict, List, Optional
from PIL import Image
from io import BytesIO
import argparse

# Configuration
SCRIPT_DIR = Path(__file__).parent
DEFAULT_INPUT = SCRIPT_DIR / "scraped_data" / "goodshort_production_data.json"
DEFAULT_OUTPUT = SCRIPT_DIR / "r2_ready"

class ProductionProcessor:
    def __init__(self, input_file: Path, output_dir: Path):
        self.input_file = input_file
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        self.stats = {
            'total_dramas': 0,
            'processed': 0,
            'covers_downloaded': 0,
            'episodes_organized': 0,
            'errors': []
        }
    
    def slugify(self, text: str) -> str:
        """Convert text to URL-safe slug"""
        text = text.lower()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '_', text)
        return text.strip('_')
    
    def download_cover(self, url: str, output_path: Path) -> bool:
        """Download and validate cover image"""
        try:
            print(f"    📥 Downloading cover...")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Validate image
            img = Image.open(BytesIO(response.content))
            width, height = img.size
            
            # Check if portrait (height > width)
            if height <= width:
                print(f"    ⚠️  Warning: Cover is not portrait ({width}x{height})")
            
            # Convert RGBA to RGB if needed
            if img.mode == 'RGBA':
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[3])
                img = rgb_img
            
            # Save as JPEG
            img.save(output_path, 'JPEG', quality=95)
            print(f"    ✅ Cover saved ({width}x{height})")
            return True
            
        except Exception as e:
            print(f"    ❌ Failed to download cover: {e}")
            self.stats['errors'].append(f"Cover download failed for {url}: {e}")
            return False
    
    def organize_episodes(self, episodes: List[Dict]) -> List[Dict]:
        """Sort episodes by order/chapterIndex"""
        if not episodes:
            return []
        
        # Try different sorting fields
        for field in ['order', 'chapterOrder', 'chapterIndex', 'episodeNumber']:
            if field in episodes[0]:
                return sorted(episodes, key=lambda x: x.get(field, 999))
        
        # Fallback: maintain original order
        return episodes
    
    def extract_episode_hls_url(self, video_urls: List[Dict], episode_id: str) -> Optional[str]:
        """Find HLS URL for specific episode"""
        for video in video_urls:
            if str(video.get('chapterId', '')) == str(episode_id):
                url = video.get('url', '')
                if '.m3u8' in url:
                    # Return base URL without token
                    return url.split('?')[0]
        return None
    
    def process_drama(self, drama_data: Dict) -> bool:
        """Process single drama"""
        book_id = drama_data.get('bookId', '')
        title = drama_data.get('title', f'Drama_{book_id}')
        
        print(f"\n{'='*70}")
        print(f"📚 Processing: {title}")
        print(f"{'='*70}")
        print(f"   ID: {book_id}")
        
        # Create drama folder
        drama_slug = self.slugify(title)
        drama_folder = self.output_dir / drama_slug
        drama_folder.mkdir(exist_ok=True)
        
        # 1. Download cover
        cover_url = drama_data.get('coverHQ') or drama_data.get('cover')
        if cover_url:
            cover_path = drama_folder / "cover.jpg"
            if self.download_cover(cover_url, cover_path):
                self.stats['covers_downloaded'] += 1
        else:
            print(f"    ⚠️  No cover URL found")
        
        # 2. Create drama metadata
        print(f"    📝 Creating metadata...")
        metadata = {
            'bookId': book_id,
            'title': title,
            'originalTitle': drama_data.get('originalTitle'),
            'description': drama_data.get('description'),
            'genre': drama_data.get('genre'),
            'category': drama_data.get('category'),
            'author': drama_data.get('author'),
            'tags': drama_data.get('tags', []),
            'totalEpisodes': drama_data.get('totalEpisodes', 0),
            'coverUrl': cover_url,
            'metadata': drama_data.get('metadata', {}),
            'source': 'GoodShort',
            'scrapedAt': drama_data.get('capturedAt')
        }
        
        metadata_path = drama_folder / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        print(f"    ✅ Metadata saved")
        
        # 3. Organize episodes
        episodes = drama_data.get('episodes', [])
        if episodes:
            print(f"    📺 Organizing {len(episodes)} episodes...")
            
            # Sort episodes
            sorted_episodes = self.organize_episodes(episodes)
            
            # Create episodes folder
            episodes_folder = drama_folder / "episodes"
            episodes_folder.mkdir(exist_ok=True)
            
            # Process each episode
            video_urls = drama_data.get('videoUrls', [])
            episode_list = []
            
            for idx, episode in enumerate(sorted_episodes, 1):
                episode_id = episode.get('id') or episode.get('chapterId') or episode.get('episodeId')
                episode_title = episode.get('title', f'Episode {idx}')
                
                # Create episode folder
                ep_folder = episodes_folder / f"ep_{idx}"
                ep_folder.mkdir(exist_ok=True)
                
                # Find HLS URL for this episode
                hls_url = self.extract_episode_hls_url(video_urls, str(episode_id))
                
                # Create episode metadata
                ep_metadata = {
                    'episodeNumber': idx,
                    'episodeId': episode_id,
                    'title': episode_title,
                    'order': episode.get('order', idx),
                    'duration': episode.get('duration'),
                    'isFree': episode.get('isFree', True),
                    'hlsUrl': hls_url,
                    'thumbnail': episode.get('thumbnail'),
                    'drama': {
                        'bookId': book_id,
                        'title': title
                    }
                }
                
                # Save episode metadata
                ep_meta_path = ep_folder / "metadata.json"
                with open(ep_meta_path, 'w', encoding='utf-8') as f:
                    json.dump(ep_metadata, f, indent=2, ensure_ascii=False)
                
                # Create playlist.m3u8 with HLS URL if available
                if hls_url:
                    playlist_path = ep_folder / "playlist.m3u8"
                    with open(playlist_path, 'w', encoding='utf-8') as f:
                        f.write(f"#EXTM3U\n#EXT-X-VERSION:3\n{hls_url}\n#EXT-X-ENDLIST\n")
                
                episode_list.append(ep_metadata)
                self.stats['episodes_organized'] += 1
            
            # Save episodes.json
            episodes_json_path = drama_folder / "episodes.json"
            with open(episodes_json_path, 'w', encoding='utf-8') as f:
                json.dump({'episodes': episode_list, 'total': len(episode_list)}, f, indent=2, ensure_ascii=False)
            
            print(f"    ✅ Organized {len(episode_list)} episodes")
        else:
            print(f"    ⚠️  No episodes found")
        
        print(f"\n✅ Drama processed: {drama_folder}")
        return True
    
    def process_all(self):
        """Process all dramas from captured data"""
        print(f"\n{'='*70}")
        print(f"🎬 GoodShort Production Data Processor")
        print(f"{'='*70}\n")
        
        # Load captured data
        print(f"📂 Loading: {self.input_file}")
        if not self.input_file.exists():
            print(f"❌ File not found: {self.input_file}")
            print(f"\n💡 Run this first:")
            print(f"   adb pull /sdcard/goodshort_production_data.json {self.input_file}")
            return
        
        with open(self.input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        dramas = data.get('dramas', {})
        self.stats['total_dramas'] = len(dramas)
        
        if not dramas:
            print(f"❌ No dramas found in captured data")
            print(f"\n💡 Capture data first using:")
            print(f"   frida -U -f com.newreading.goodreels -l frida/production-scraper.js")
            return
        
        print(f"✅ Found {len(dramas)} dramas\n")
        
        # Process each drama
        for book_id, drama_data in dramas.items():
            try:
                if self.process_drama(drama_data):
                    self.stats['processed'] += 1
            except Exception as e:
                print(f"❌ Error processing drama {book_id}: {e}")
                self.stats['errors'].append(f"Drama {book_id}: {e}")
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print processing summary"""
        print(f"\n{'='*70}")
        print(f"✅ PROCESSING COMPLETE")
        print(f"{'='*70}")
        print(f"\n📊 Statistics:")
        print(f"  - Total Dramas: {self.stats['total_dramas']}")
        print(f"  - Processed: {self.stats['processed']}")
        print(f"  - Covers Downloaded: {self.stats['covers_downloaded']}")
        print(f"  - Episodes Organized: {self.stats['episodes_organized']}")
        
        if self.stats['errors']:
            print(f"\n⚠️  Errors: {len(self.stats['errors'])}")
            for error in self.stats['errors'][:5]:
                print(f"  - {error}")
            if len(self.stats['errors']) > 5:
                print(f"  ... and {len(self.stats['errors']) - 5} more")
        
        print(f"\n📁 Output: {self.output_dir}")
        print(f"\n🎯 Next Steps:")
        print(f"1. Review output in: {self.output_dir}")
        print(f"2. (Optional) Download videos using HTTP Toolkit headers")
        print(f"3. Upload to R2: python upload_to_r2.py")
        print()

def main():
    parser = argparse.ArgumentParser(description='Process GoodShort production captured data')
    parser.add_argument('--input', type=Path, default=DEFAULT_INPUT, help='Input JSON file')
    parser.add_argument('--output', type=Path, default=DEFAULT_OUTPUT, help='Output directory')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be processed without actually processing')
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("🔍 DRY RUN MODE - No files will be created")
        if args.input.exists():
            with open(args.input, 'r', encoding='utf-8') as f:
                data = json.load(f)
            dramas = data.get('dramas', {})
            print(f"\nWould process {len(dramas)} dramas:")
            for book_id, drama in dramas.items():
                title = drama.get('title', 'Unknown')
                episodes = len(drama.get('episodes', []))
                print(f"  - {title} ({episodes} episodes)")
        else:
            print(f"❌ Input file not found: {args.input}")
        return
    
    processor = ProductionProcessor(args.input, args.output)
    processor.process_all()

if __name__ == "__main__":
    main()
