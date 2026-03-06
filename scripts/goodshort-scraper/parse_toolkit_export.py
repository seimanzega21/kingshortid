#!/usr/bin/env python3
"""
HTTP TOOLKIT PARSER
===================

Parses HTTP Toolkit HAR export to extract video segment URLs.

Usage:
    1. In HTTP Toolkit, File > Export > Save as HAR
    2. python parse_toolkit_export.py captured.har
"""

import json
import sys
from pathlib import Path
from urllib.parse import urlparse
from collections import defaultdict

def parse_har(har_file: Path):
    """Parse HAR file and extract .ts segment URLs"""
    
    with open(har_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    segments = defaultdict(list)
    playlists = []
    
    print(f"\n{'='*70}")
    print(f"Parsing: {har_file.name}")
    print(f"{'='*70}\n")
    
    # Extract from HAR entries
    entries = data.get('log', {}).get('entries', [])
    
    print(f"Total HTTP requests: {len(entries)}")
    
    for entry in entries:
        url = entry['request']['url']
        
        # Check for m3u8 playlist
        if '.m3u8' in url and 'goodreels.com' in url:
            playlists.append(url)
            print(f"✅ Playlist: {url}")
        
        # Check for .ts segments
        if url.endswith('.ts') and 'goodreels.com' in url:
            # Try to extract episode info from URL
            episode_id = extract_episode_id(url)
            segments[episode_id].append(url)
    
    print(f"\n{'='*70}")
    print(f"Results:")
    print(f"{'='*70}")
    print(f"Playlists found: {len(playlists)}")
    print(f"Episodes with segments: {len(segments)}")
    
    for ep_id, urls in segments.items():
        print(f"  Episode {ep_id}: {len(urls)} segments")
    
    # Save results
    output = {
        'playlists': playlists,
        'segments': {k: v for k, v in segments.items()}
    }
    
    output_file = har_file.parent / "extracted_urls.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Saved to: {output_file}")
    print(f"\nNext: python download_segments.py extracted_urls.json")
    
    return output

def extract_episode_id(url: str) -> str:
    """Try to extract episode ID from URL"""
    # Example: .../614590/... → episode 614590
    parts = url.split('/')
    for i, part in enumerate(parts):
        if part.isdigit() and len(part) > 5:
            return part
    return "unknown"

def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_toolkit_export.py <har_file>")
        print("\nExample:")
        print("  python parse_toolkit_export.py captured_requests.har")
        return
    
    har_file = Path(sys.argv[1])
    
    if not har_file.exists():
        print(f"❌ File not found: {har_file}")
        return
    
    parse_har(har_file)

if __name__ == "__main__":
    main()
