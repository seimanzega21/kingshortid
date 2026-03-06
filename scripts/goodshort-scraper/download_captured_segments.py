#!/usr/bin/env python3
"""
HTTP TOOLKIT AUTOMATION - Video Segment Downloader
===================================================

Downloads all video segments captured by HTTP Toolkit.
Works by monitoring HTTP Toolkit's network capture in real-time!

BREAKTHROUGH: We can download segments using correct headers!
"""

import subprocess
import time
import re
from pathlib import Path
import requests
from datetime import datetime

# Config
OUTPUT_DIR = Path("captured_videos")
OUTPUT_DIR.mkdir(exist_ok=True)

# Headers that work (from HTTP Toolkit capture)
HEADERS = {
    'User-Agent': 'com.newreading.goodreels/2.7.8.2078 (Linux;Android 11) ExoPlayerLib/2.18.2',
    'Accept-Encoding': 'identity',
    'Connection': 'Keep-Alive'
}

class VideoSegmentCapture:
    """Capture and download video segments"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.captured_episodes = {}
    
    def download_segment(self, url: str, episode_folder: Path, segment_num: int):
        """Download single segment"""
        
        filename = f"segment_{segment_num:06d}.ts"
        output_path = episode_folder / filename
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            size_kb = len(response.content) / 1024
            return True, size_kb
            
        except Exception as e:
            return False, 0
    
    def extract_episode_id(self, url: str) -> str:
        """Extract episode ID from URL"""
        # Pattern: /books/260/31000762260/325922/...
        match = re.search(r'/books/\d+/\d+/(\d+)/', url)
        if match:
            return match.group(1)
        return "unknown"
    
    def download_from_url_list(self, url_file: Path):
        """Download from list of URLs"""
        
        if not url_file.exists():
            print(f"❌ URL file not found: {url_file}")
            return
        
        with open(url_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip() and line.startswith('http')]
        
        if not urls:
            print("❌ No URLs found in file")
            return
        
        print(f"\n{'='*70}")
        print(f"DOWNLOADING {len(urls)} SEGMENTS")
        print(f"{'='*70}\n")
        
        # Group by episode
        episodes = {}
        for url in urls:
            ep_id = self.extract_episode_id(url)
            if ep_id not in episodes:
                episodes[ep_id] = []
            episodes[ep_id].append(url)
        
        print(f"Found {len(episodes)} episode(s)\n")
        
        # Download by episode
        total_success = 0
        total_failed = 0
        
        for ep_id, ep_urls in episodes.items():
            print(f"Episode {ep_id}: {len(ep_urls)} segments")
            
            ep_folder = OUTPUT_DIR / f"episode_{ep_id}"
            ep_folder.mkdir(exist_ok=True)
            
            for i, url in enumerate(ep_urls):
                success, size = self.download_segment(url, ep_folder, i)
                
                if success:
                    print(f"  [{i+1}/{len(ep_urls)}] ✅ segment_{i:06d}.ts ({size:.1f} KB)")
                    total_success += 1
                else:
                    print(f"  [{i+1}/{len(ep_urls)}] ❌ Failed")
                    total_failed += 1
            
            print()
        
        print(f"{'='*70}")
        print(f"COMPLETE!")
        print(f"{'='*70}")
        print(f"Success: {total_success}")
        print(f"Failed: {total_failed}")
        print(f"Output: {OUTPUT_DIR}/")
        print()

def main():
    """Main entry point"""
    
    capturer = VideoSegmentCapture()
    
    # Check for URL list
    url_file = Path("segment_urls.txt")
    
    if url_file.exists():
        capturer.download_from_url_list(url_file)
    else:
        print(f"\n{'='*70}")
        print(f"HTTP TOOLKIT SEGMENT DOWNLOADER")
        print(f"{'='*70}\n")
        print("USAGE:")
        print()
        print("1. In HTTP Toolkit, filter for .ts requests")
        print("2. Copy all .ts URLs")
        print("3. Paste into: segment_urls.txt (one URL per line)")
        print("4. Run this script again")
        print()
        print("OR use manual HAR export if available")
        print()

if __name__ == "__main__":
    main()
