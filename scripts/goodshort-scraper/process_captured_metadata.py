#!/usr/bin/env python3
"""
Process Captured Metadata from Frida Script

This script:
1. Reads the JSON output from capture-metadata-enhanced.js
2. Downloads cover images
3. Organizes metadata into structured format
4. Updates books_metadata.json with complete info

Usage:
    python process_captured_metadata.py [input_json_file]
    
    If no input file specified, looks for metadata_complete.json
"""

import json
import os
import sys
import requests
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse
import time

# Paths
SCRIPT_DIR = Path(__file__).parent
SCRAPED_DATA_DIR = SCRIPT_DIR / "scraped_data"
METADATA_DIR = SCRAPED_DATA_DIR / "metadata"
COVERS_DIR = SCRAPED_DATA_DIR / "covers"
OUTPUT_FILE = SCRAPED_DATA_DIR / "books_metadata.json"

# Ensure directories exist
METADATA_DIR.mkdir(parents=True, exist_ok=True)
COVERS_DIR.mkdir(parents=True, exist_ok=True)


def download_cover(url: str, book_id: str) -> str | None:
    """Download cover image and return local path."""
    if not url:
        return None
    
    try:
        # Get file extension from URL
        parsed = urlparse(url)
        path_parts = parsed.path.split('/')
        filename = path_parts[-1].split('?')[0]  # Remove query params
        ext = filename.split('.')[-1] if '.' in filename else 'jpg'
        
        local_filename = f"{book_id}_cover.{ext}"
        local_path = COVERS_DIR / local_filename
        
        if local_path.exists():
            print(f"  [SKIP] Cover already exists: {local_filename}")
            return str(local_path)
        
        print(f"  [DOWNLOAD] {url[:60]}...")
        
        headers = {
            'User-Agent': 'okhttp/4.9.3',
            'Accept': 'image/*'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        with open(local_path, 'wb') as f:
            f.write(response.content)
        
        print(f"  [OK] Saved: {local_filename} ({len(response.content)} bytes)")
        return str(local_path)
        
    except Exception as e:
        print(f"  [ERROR] Failed to download cover: {e}")
        return None


def process_captured_data(input_file: str) -> dict:
    """Process captured data from Frida script."""
    
    print(f"\n{'='*60}")
    print("📚 Processing Captured Metadata")
    print(f"{'='*60}\n")
    
    # Load input JSON
    with open(input_file, 'r', encoding='utf-8') as f:
        captured = json.load(f)
    
    dramas = captured.get('dramas', {})
    covers = captured.get('covers', {})
    stats = captured.get('stats', {})
    
    print(f"📊 Input Stats:")
    print(f"   Total dramas: {len(dramas)}")
    print(f"   Total covers: {len(covers)}")
    print(f"   Dramas with metadata: {stats.get('dramasWithFullMetadata', 0)}")
    print()
    
    # Load existing metadata
    existing_metadata = {}
    if OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            existing_metadata = json.load(f)
        print(f"📂 Loaded {len(existing_metadata)} existing entries\n")
    
    # Process each drama
    processed_count = 0
    updated_count = 0
    cover_download_count = 0
    
    for book_id, drama in dramas.items():
        print(f"\n🎬 Processing: {drama.get('title', 'Unknown')} ({book_id})")
        
        metadata = drama.get('metadata', {}) or {}
        
        # Build structured metadata
        entry = {
            'bookId': book_id,
            'title': metadata.get('title') or drama.get('title') or f"Drama {book_id}",
            'cover': None,
            'coverLocal': None,
            'description': metadata.get('description', ''),
            'author': metadata.get('author'),
            'category': metadata.get('category'),
            'genre': metadata.get('category'),  # Alias
            'tags': metadata.get('tags', []),
            'totalChapters': metadata.get('totalChapters', 0),
            'views': metadata.get('views', 0),
            'likes': metadata.get('likes', 0),
            'rating': metadata.get('rating'),
            'status': metadata.get('status'),
            'language': metadata.get('language', 'id'),
            'source': 'goodshort',
            'episodesCaptured': len(drama.get('episodes', {})),
            'chapterList': drama.get('chapterList'),
            'needsUpdate': False,
            'lastUpdated': datetime.now().isoformat()
        }
        
        # Get cover URL (prefer HQ)
        cover_url = drama.get('coverHQ') or drama.get('cover')
        
        # Also check covers dict
        if not cover_url and book_id in covers:
            cover_sizes = covers[book_id]
            # Prefer larger sizes
            for size in ['1080', '720', '540', '360', '']:
                for key, url in cover_sizes.items():
                    if size in key:
                        cover_url = url
                        break
                if cover_url:
                    break
        
        entry['cover'] = cover_url
        
        # Download cover if available
        if cover_url:
            local_cover = download_cover(cover_url, book_id)
            if local_cover:
                entry['coverLocal'] = local_cover
                cover_download_count += 1
        
        # Check if update needed
        if book_id in existing_metadata:
            old = existing_metadata[book_id]
            if entry['title'] != old.get('title') or entry['cover'] != old.get('cover'):
                updated_count += 1
                print(f"  [UPDATE] Metadata changed")
        
        existing_metadata[book_id] = entry
        processed_count += 1
        
        # Rate limit for cover downloads
        if cover_url:
            time.sleep(0.5)
    
    # Save updated metadata
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(existing_metadata, f, indent=2, ensure_ascii=False)
    
    # Also save individual drama files
    for book_id, entry in existing_metadata.items():
        drama_file = METADATA_DIR / f"{book_id}.json"
        with open(drama_file, 'w', encoding='utf-8') as f:
            json.dump(entry, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print("✅ PROCESSING COMPLETE")
    print(f"{'='*60}")
    print(f"   Processed: {processed_count} dramas")
    print(f"   Updated:   {updated_count} entries")
    print(f"   Covers:    {cover_download_count} downloaded")
    print(f"   Output:    {OUTPUT_FILE}")
    print(f"{'='*60}\n")
    
    return existing_metadata


def main():
    # Determine input file
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        # Look for default files
        candidates = [
            SCRAPED_DATA_DIR / "metadata_complete.json",
            SCRIPT_DIR / "metadata_complete.json",
            SCRAPED_DATA_DIR / "captured_metadata.json"
        ]
        
        input_file = None
        for candidate in candidates:
            if candidate.exists():
                input_file = str(candidate)
                break
        
        if not input_file:
            print("ERROR: No input file found!")
            print(f"Expected one of: {[str(c) for c in candidates]}")
            print("\nUsage: python process_captured_metadata.py [input.json]")
            print("\nTo get the JSON data:")
            print("  1. Run start-capture-enhanced.bat")
            print("  2. Browse dramas in the GoodReels app")
            print("  3. Type 'save()' in Frida console")
            print("  4. Copy the JSON output to metadata_complete.json")
            sys.exit(1)
    
    process_captured_data(input_file)


if __name__ == "__main__":
    main()
