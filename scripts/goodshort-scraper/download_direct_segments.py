#!/usr/bin/env python3
"""
Download .ts segments directly from complete_capture.json
Using HTTP Toolkit headers (already tested & working!)
"""

import json
import requests
from pathlib import Path
from collections import defaultdict
import subprocess

SCRIPT_DIR = Path(__file__).parent
CAPTURE_FILE = SCRIPT_DIR / "scraped_data" / "complete_capture.json"
HEADERS_FILE = SCRIPT_DIR / "http_toolkit_headers.json"
OUTPUT_DIR = SCRIPT_DIR / "r2_ready"

def load_headers():
    """Load HTTP Toolkit headers"""
    with open(HEADERS_FILE, 'r') as f:
        return json.load(f)

def download_segment(url, output_path, headers, retries=3):
    """Download single .ts segment"""
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            return True, len(response.content)
            
        except Exception as e:
            if attempt < retries - 1:
                print(f"      ⚠️  Retry {attempt + 1}/{retries}")
            else:
                print(f"      ❌ Failed: {e}")
                return False, 0
    
    return False, 0

def combine_segments(segments_folder, output_video):
    """Combine .ts segments into MP4"""
    try:
        print(f"\n  🔧 Combining segments...")
        
        # Create concat file
        concat_file = segments_folder / "concat.txt"
        segments = sorted(segments_folder.glob("segment_*.ts"))
        
        if not segments:
            print(f"  ❌ No segments found in {segments_folder}")
            return False
        
        with open(concat_file, 'w', encoding='utf-8') as f:
            for segment in segments:
                f.write(f"file '{segment.absolute()}'\n")
        
        # Run ffmpeg
        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(concat_file),
            '-c', 'copy',
            '-y',
            str(output_video)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0 and output_video.exists():
            size_mb = output_video.stat().st_size / 1024 / 1024
            print(f"  ✅ Video: {output_video.name} ({size_mb:.2f} MB)")
            return True
        else:
            print(f"  ❌ ffmpeg failed")
            return False
            
    except FileNotFoundError:
        print(f"  ⚠️  ffmpeg not found - segments saved but not combined")
        print(f"      Download: https://ffmpeg.org/download.html")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False

def main():
    print(f"\n{'='*70}")
    print(f"🎥 Direct .ts Segment Downloader")
    print(f"{'='*70}\n")
    
    # Load headers
    print(f"📋 Loading HTTP Toolkit headers...")
    headers = load_headers()
    print(f"✅ Headers loaded: {list(headers.keys())}\n")
    
    # Load capture data
    print(f"📂 Loading complete_capture.json...")
    with open(CAPTURE_FILE, 'r') as f:
        data = json.load(f)
    
    video_urls = data.get('videoUrls', [])
    
    # Filter only .ts files
    ts_segments = [v for v in video_urls if v['url'].endswith('.ts')]
    print(f"✅ Found {len(ts_segments)} .ts segments\n")
    
    # Group by episode (book + chapter)
    episodes = defaultdict(list)
    for segment in ts_segments:
        book_id = segment['bookId']
        chapter_id = segment['chapterId']
        key = f"{book_id}_{chapter_id}"
        episodes[key].append(segment)
    
    print(f"📺 Episodes: {len(episodes)}\n")
    
    # Download each episode
    total_downloaded = 0
    total_size = 0
    
    for episode_key, segments in episodes.items():
        book_id, chapter_id = episode_key.split('_')
        
        print(f"{'='*70}")
        print(f"📚 Book {book_id[-6:]} - Episode {chapter_id}")
        print(f"{'='*70}")
        print(f"  Segments: {len(segments)}")
        
        # Find drama folder
        drama_folder = OUTPUT_DIR / f"drama_{book_id[-6:]}"
        if not drama_folder.exists():
            print(f"  ⚠️  Drama folder not found, skipping...")
            continue
        
        # Find episode folder
        ep_folders = list((drama_folder / "episodes").glob("ep_*"))
        if not ep_folders:
            print(f"  ⚠️  No episode folders, skipping...")
            continue
        
        ep_folder = ep_folders[0]  # Use first episode (we only have 1 per drama)
        
        # Create segments folder
        segments_folder = ep_folder / "segments"
        segments_folder.mkdir(exist_ok=True)
        
        # Download segments
        print(f"\n  📥 Downloading segments...")
        downloaded = 0
        
        for idx, segment in enumerate(segments):
            url = segment['url']
            output_file = segments_folder / f"segment_{idx:06d}.ts"
            
            if output_file.exists():
                downloaded += 1
                continue
            
            if idx % 10 == 0:
                print(f"    [{idx}/{len(segments)}]", end='', flush=True)
            
            success, size = download_segment(url, output_file, headers)
            if success:
                downloaded += 1
                total_size += size
                if idx % 10 == 0:
                    print(f" ✅ {size/1024:.1f} KB")
            else:
                if idx % 10 == 0:
                    print(f" ❌")
        
        print(f"\n  ✅ Downloaded: {downloaded}/{len(segments)} segments")
        total_downloaded += downloaded
        
        # Combine to video
        if downloaded == len(segments):
            output_video = ep_folder / "video.mp4"
            combine_segments(segments_folder, output_video)
        else:
            print(f"  ⚠️  Incomplete - skipping combine")
    
    # Summary
    print(f"\n{'='*70}")
    print(f"✅ DOWNLOAD COMPLETE")
    print(f"{'='*70}")
    print(f"\n📊 Summary:")
    print(f"  - Episodes: {len(episodes)}")
    print(f"  - Segments: {total_downloaded}")
    print(f"  - Size: {total_size/1024/1024:.2f} MB")
    print(f"\n📁 Output: {OUTPUT_DIR}")
    print(f"\n🎯 Next: Upload to R2")
    print(f"   python upload_to_r2.py")
    print()

if __name__ == "__main__":
    main()
