#!/usr/bin/env python3
"""
MITM VIDEO DUMPER - Save .ts segments automatically
====================================================

Based on user recommendation: MITM Dumping is the BEST approach!

How it works:
1. mitmproxy sits between app and server
2. App makes valid requests (has tokens)
3. Proxy saves .ts files to disk
4. App receives response normally

Usage:
    mitmdump -s mitm_video_dumper.py
    
Then run ADB automation to play episodes.
"""

from mitmproxy import http
from pathlib import Path
import re
import json

# Configuration
OUTPUT_DIR = Path("d:/kingshortid/scripts/goodshort-scraper/captured_segments")
OUTPUT_DIR.mkdir(exist_ok=True)

# Track episodes
current_episode = {
    'id': None,
    'segment_count': 0
}

# Stats
stats = {
    'segments_saved': 0,
    'bytes_saved': 0,
    'episodes': set()
}

def extract_episode_info(url: str):
    """Extract episode ID from URL"""
    # Pattern: /books/963/31001221963/614590/...
    match = re.search(r'/books/\d+/\d+/(\d+)/', url)
    if match:
        return match.group(1)
    return None

def response(flow: http.HTTPFlow) -> None:
    """
    Called for every HTTP response.
    Saves .ts video segments to disk.
    """
    url = flow.request.pretty_url
    
    # Check if this is a m3u8 playlist
    if url.endswith('.m3u8') and 'goodreels.com' in url:
        episode_id = extract_episode_info(url)
        if episode_id and episode_id != current_episode['id']:
            # New episode detected
            current_episode['id'] = episode_id
            current_episode['segment_count'] = 0
            stats['episodes'].add(episode_id)
            
            print(f"\n{'='*70}")
            print(f"🎬 NEW EPISODE DETECTED: {episode_id}")
            print(f"{'='*70}\n")
    
    # Check if this is a video segment
    if url.endswith('.ts') and 'goodreels.com' in url:
        episode_id = extract_episode_info(url)
        
        if not episode_id:
            episode_id = current_episode.get('id', 'unknown')
        
        # Create episode folder
        episode_folder = OUTPUT_DIR / f"episode_{episode_id}"
        episode_folder.mkdir(exist_ok=True)
        
        # Generate filename
        segment_num = current_episode['segment_count']
        filename = f"goodshort_{segment_num:06d}.ts"
        output_path = episode_folder / filename
        
        # Save segment
        try:
            with open(output_path, 'wb') as f:
                f.write(flow.response.content)
            
            file_size = len(flow.response.content)
            stats['segments_saved'] += 1
            stats['bytes_saved'] += file_size
            current_episode['segment_count'] += 1
            
            # Progress indicator
            if segment_num % 10 == 0:
                print(f"  📺 Episode {episode_id}: Saved {segment_num} segments ({stats['bytes_saved'] / 1024 / 1024:.1f} MB)")
            
        except Exception as e:
            print(f"  ❌ Error saving {filename}: {e}")

def done():
    """Called when mitmproxy shuts down"""
    print(f"\n{'='*70}")
    print(f"✅ MITM DUMPING COMPLETE!")
    print(f"{'='*70}\n")
    print(f"📊 Statistics:")
    print(f"  Episodes captured: {len(stats['episodes'])}")
    print(f"  Segments saved: {stats['segments_saved']}")
    print(f"  Total data: {stats['bytes_saved'] / 1024 / 1024:.2f} MB")
    print(f"\n📁 Output: {OUTPUT_DIR}")
    print()
