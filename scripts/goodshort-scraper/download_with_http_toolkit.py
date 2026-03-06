#!/usr/bin/env python3
"""
GoodShort Video Downloader - HTTP Toolkit Edition
==================================================

Download video segments using headers captured from HTTP Toolkit.

This script helps you:
1. Load headers from HTTP Toolkit cURL export
2. Download HLS segments with proper authentication
3. Combine segments into MP4 videos

Usage:
    # Step 1: Export headers from HTTP Toolkit
    # Right-click .ts request -> Copy as cURL -> Paste to curl_export.txt
    
    # Step 2: Parse headers
    python download_with_http_toolkit.py --parse-curl curl_export.txt
    
    # Step 3: Download videos
    python download_with_http_toolkit.py --drama-folder r2_ready/jenderal_jadi_tukang
"""

import json
import os
import re
import requests
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import argparse
import shlex

SCRIPT_DIR = Path(__file__).parent
HEADERS_FILE = SCRIPT_DIR / "http_toolkit_headers.json"

def parse_curl_to_headers(curl_command: str) -> Dict[str, str]:
    """Extract headers from cURL command"""
    headers = {}
    
    # Find all -H or --header arguments
    header_pattern = r"-H\s+'([^']+)'|--header\s+'([^']+)'"
    matches = re.findall(header_pattern, curl_command)
    
    for match in matches:
        header = match[0] or match[1]
        if ':' in header:
            key, value = header.split(':', 1)
            headers[key.strip()] = value.strip()
    
    return headers

def save_headers(headers: Dict[str, str], output_file: Path):
    """Save headers to JSON file"""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(headers, f, indent=2)
    print(f"✅ Headers saved to: {output_file}")
    print(f"\n📋 Extracted headers:")
    for key, value in headers.items():
        # Mask sensitive values
        if 'token' in key.lower() or 'auth' in key.lower():
            display_value = value[:20] + '...' if len(value) > 20 else value
        else:
            display_value = value
        print(f"  {key}: {display_value}")

def load_headers(headers_file: Path) -> Dict[str, str]:
    """Load headers from JSON file"""
    if not headers_file.exists():
        print(f"❌ Headers file not found: {headers_file}")
        print(f"\n💡 Extract headers first:")
        print(f"   python {Path(__file__).name} --parse-curl curl_export.txt")
        return {}
    
    with open(headers_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def download_segment(url: str, output_path: Path, headers: Dict[str, str], retries: int = 3) -> bool:
    """Download single .ts segment"""
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            return True
            
        except Exception as e:
            if attempt < retries - 1:
                print(f"    ⚠️  Retry {attempt + 1}/{retries}: {e}")
            else:
                print(f"    ❌ Failed after {retries} attempts: {e}")
                return False
    
    return False

def parse_m3u8_playlist(playlist_url: str, headers: Dict[str, str]) -> List[str]:
    """Parse HLS playlist to get segment URLs"""
    try:
        response = requests.get(playlist_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        content = response.text
        base_url = '/'.join(playlist_url.split('/')[:-1])
        
        segments = []
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                # Check if absolute or relative URL
                if line.startswith('http'):
                    segments.append(line)
                else:
                    segments.append(f"{base_url}/{line}")
        
        return segments
        
    except Exception as e:
        print(f"❌ Failed to parse playlist: {e}")
        return []

def download_episode(episode_folder: Path, headers: Dict[str, str]) -> bool:
    """Download all segments for an episode"""
    metadata_file = episode_folder / "metadata.json"
    if not metadata_file.exists():
        print(f"  ⚠️  No metadata.json found")
        return False
    
    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    hls_url = metadata.get('hlsUrl')
    if not hls_url:
        print(f"  ⚠️  No HLS URL in metadata")
        return False
    
    episode_num = metadata.get('episodeNumber', 0)
    print(f"  📥 Downloading Episode {episode_num}...")
    
    # Parse playlist to get segment URLs
    segments = parse_m3u8_playlist(hls_url, headers)
    if not segments:
        print(f"  ❌ No segments found in playlist")
        return False
    
    print(f"  📊 Found {len(segments)} segments")
    
    # Create segments folder
    segments_folder = episode_folder / "segments"
    segments_folder.mkdir(exist_ok=True)
    
    # Download each segment
    downloaded = 0
    for idx, segment_url in enumerate(segments):
        segment_file = segments_folder / f"segment_{idx:06d}.ts"
        
        if segment_file.exists():
            downloaded += 1
            continue
        
        if idx % 10 == 0:
            print(f"    Progress: {idx}/{len(segments)}")
        
        if download_segment(segment_url, segment_file, headers):
            downloaded += 1
        else:
            print(f"    ❌ Failed: segment {idx}")
    
    print(f"  ✅ Downloaded: {downloaded}/{len(segments)} segments")
    
    # Combine segments to MP4
    if downloaded == len(segments):
        return combine_segments(segments_folder, episode_folder / "video.mp4")
    
    return False

def combine_segments(segments_folder: Path, output_file: Path) -> bool:
    """Combine .ts segments into single MP4"""
    try:
        print(f"  🔧 Combining segments...")
        
        # Create concat file
        concat_file = segments_folder / "concat.txt"
        segments = sorted(segments_folder.glob("segment_*.ts"))
        
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
            str(output_file)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Get file size
            size_mb = output_file.stat().st_size / 1024 / 1024
            print(f"  ✅ Video created: {output_file.name} ({size_mb:.2f} MB)")
            return True
        else:
            print(f"  ❌ ffmpeg failed: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print(f"  ❌ ffmpeg not found. Install: https://ffmpeg.org/download.html")
        return False
    except Exception as e:
        print(f"  ❌ Failed to combine: {e}")
        return False

def download_drama(drama_folder: Path, headers: Dict[str, str]):
    """Download all episodes for a drama"""
    print(f"\n{'='*70}")
    print(f"📚 Processing: {drama_folder.name}")
    print(f"{'='*70}\n")
    
    episodes_folder = drama_folder / "episodes"
    if not episodes_folder.exists():
        print(f"❌ No episodes folder found")
        return
    
    episode_folders = sorted(episodes_folder.glob("ep_*"))
    print(f"📺 Found {len(episode_folders)} episodes\n")
    
    for ep_folder in episode_folders:
        download_episode(ep_folder, headers)

def main():
    parser = argparse.ArgumentParser(description='Download GoodShort videos using HTTP Toolkit headers')
    parser.add_argument('--parse-curl', type=Path, help='Parse cURL export file and save headers')
    parser.add_argument('--drama-folder', type=Path, help='Download videos for drama folder')
    parser.add_argument('--headers', type=Path, default=HEADERS_FILE, help='Headers JSON file')
    
    args = parser.parse_args()
    
    # Parse cURL to extract headers
    if args.parse_curl:
        if not args.parse_curl.exists():
            print(f"❌ File not found: {args.parse_curl}")
            return
        
        print(f"📋 Parsing cURL from: {args.parse_curl}")
        with open(args.parse_curl, 'r', encoding='utf-8') as f:
            curl_command = f.read()
        
        headers = parse_curl_to_headers(curl_command)
        
        if not headers:
            print(f"❌ No headers found in cURL command")
            print(f"\n💡 Make sure you copied the FULL cURL command from HTTP Toolkit")
            return
        
        save_headers(headers, args.headers)
        return
    
    # Download drama videos
    if args.drama_folder:
        headers = load_headers(args.headers)
        if not headers:
            return
        
        if not args.drama_folder.exists():
            print(f"❌ Drama folder not found: {args.drama_folder}")
            return
        
        download_drama(args.drama_folder, headers)
        return
    
    # No arguments provided
    parser.print_help()
    print(f"\n💡 Quick Start:")
    print(f"1. Copy .ts request from HTTP Toolkit as cURL")
    print(f"2. Save to file: curl_export.txt")
    print(f"3. Run: python {Path(__file__).name} --parse-curl curl_export.txt")
    print(f"4. Run: python {Path(__file__).name} --drama-folder r2_ready/drama_name")

if __name__ == "__main__":
    main()
