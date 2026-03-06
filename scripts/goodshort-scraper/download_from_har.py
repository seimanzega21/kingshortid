#!/usr/bin/env python3
"""
HTTP TOOLKIT SEGMENT DOWNLOADER
================================

Downloads all .ts segments from HTTP Toolkit HAR export.
"""

import json
import requests
from pathlib import Path
from urllib.parse import urlparse
import re

# Config
HAR_FILE = Path("goodshort_capture.har")
OUTPUT_DIR = Path("downloaded_segments")
OUTPUT_DIR.mkdir(exist_ok=True)

def parse_har(har_path):
    """Extract .ts URLs from HAR file"""
    
    with open(har_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    entries = data.get('log', {}).get('entries', [])
    
    segments = []
    for entry in entries:
        url = entry['request']['url']
        
        # Check if .ts segment
        if url.endswith('.ts') and 'goodreels.com' in url:
            segments.append({
                'url': url,
                'status': entry['response']['status'],
                'size': entry['response']['content'].get('size', 0)
            })
    
    return segments

def download_segments(segments):
    """Download all segments"""
    
    print(f"\n{'='*70}")
    print(f"DOWNLOADING {len(segments)} SEGMENTS")
    print(f"{'='*70}\n")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'GoodShort/2.5.1 (Linux; Android 11)',
        'Accept': '*/*'
    })
    
    success = 0
    failed = 0
    
    for i, seg in enumerate(segments):
        url = seg['url']
        filename = f"segment_{i:06d}.ts"
        output_path = OUTPUT_DIR / filename
        
        try:
            print(f"[{i+1}/{len(segments)}] Downloading {filename}...", end=' ')
            
            response = session.get(url, timeout=30)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            size_mb = len(response.content) / 1024 / 1024
            print(f"✅ ({size_mb:.2f} MB)")
            success += 1
            
        except Exception as e:
            print(f"❌ {e}")
            failed += 1
    
    print(f"\n{'='*70}")
    print(f"COMPLETE!")
    print(f"{'='*70}")
    print(f"Success: {success}")
    print(f"Failed: {failed}")
    print(f"Output: {OUTPUT_DIR}/")
    print()

def main():
    if not HAR_FILE.exists():
        print(f"\n❌ HAR file not found: {HAR_FILE}")
        print()
        print("PLEASE EXPORT FROM HTTP TOOLKIT:")
        print("  1. In HTTP Toolkit, click 'File' → 'Export'")
        print("  2. Choose format: HAR")
        print(f"  3. Save as: {HAR_FILE.absolute()}")
        print("  4. Run this script again")
        print()
        return
    
    print(f"\n{'='*70}")
    print(f"HTTP TOOLKIT SEGMENT DOWNLOADER")
    print(f"{'='*70}\n")
    
    print(f"Parsing HAR file: {HAR_FILE}")
    segments = parse_har(HAR_FILE)
    
    print(f"Found {len(segments)} video segments")
    
    if segments:
        download_segments(segments)
    else:
        print("\n❌ No .ts segments found in HAR file")

if __name__ == "__main__":
    main()
