#!/usr/bin/env python3
"""
Extract Drama Metadata and Covers from HAR Files
=================================================

Extracts complete metadata and cover URLs from HTTP Toolkit HAR files
to enrich the r2_ready folder structure.

Usage:
    python enrich_r2_ready_from_har.py
"""

import json
import os
import re
import requests
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse, parse_qs

# Configuration
SCRIPT_DIR = Path(__file__).parent
HAR_FILE = SCRIPT_DIR / "HTTPToolkit_2026-02-01_23-48.har"
R2_READY_DIR = SCRIPT_DIR / "r2_ready"

def extract_book_id_from_url(url: str) -> Optional[str]:
    """Extract bookId from GoodReels URL"""
    # Pattern: /books/xxx/31001051678/...
    match = re.search(r'/books/\d+/(\d+)/', url)
    if match:
        return match.group(1)
    return None

def extract_metadata_from_har(har_file: Path) -> Dict:
    """Extract drama metadata and cover URLs from HAR file"""
    print(f"\n📖 Reading HAR file: {har_file.name}")
    
    with open(har_file, 'r', encoding='utf-8') as f:
        har_data = json.load(f)
    
    entries = har_data['log']['entries']
    dramas = {}
    
    print(f"   Found {len(entries)} HTTP requests to analyze...\n")
    
    for entry in entries:
        request = entry['request']
        response = entry['response']
        url = request['url']
        
        # Look for API responses with drama metadata
        if 'book/details' in url or 'book/info' in url:
            try:
                if response['content'].get('text'):
                    response_text = response['content']['text']
                    data = json.loads(response_text)
                    
                    if 'data' in data and data['data']:
                        book_data = data['data']
                        book_id = str(book_data.get('id', ''))
                        
                        if book_id and book_id.startswith('31'):
                            dramas[book_id] = {
                                'bookId': book_id,
                                'title': book_data.get('title', f'Drama {book_id[-6:]}'),
                                'description': book_data.get('description', book_data.get('intro', '')),
                                'coverUrl': book_data.get('cover', book_data.get('coverUrl', '')),
                                'genre': book_data.get('categoryName', 'Drama'),
                                'tags': book_data.get('tags', []),
                                'totalEpisodes': book_data.get('chapterNum', 0),
                                'author': book_data.get('author', 'GoodShort'),
                            }
                            print(f"   ✅ Found: {dramas[book_id]['title']} (ID: {book_id})")
            except:
                pass
        
        # Look for cover images
        if 'cover' in url.lower() and ('.jpg' in url or '.png' in url or '.webp' in url):
            book_id = extract_book_id_from_url(url)
            if book_id and book_id in dramas:
                if not dramas[book_id].get('coverUrl'):
                    dramas[book_id]['coverUrl'] = url
                    print(f"   📸 Cover URL for {book_id}: {url[:60]}...")
    
    return dramas

def download_cover(cover_url: str, output_path: Path) -> bool:
    """Download cover image from URL"""
    try:
        print(f"      Downloading cover...")
        response = requests.get(cover_url, timeout=30)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        size_kb = output_path.stat().st_size / 1024
        print(f"      ✅ Saved cover.jpg ({size_kb:.1f} KB)")
        return True
        
    except Exception as e:
        print(f"      ❌ Download failed: {e}")
        return False

def enrich_r2_ready(dramas_metadata: Dict):
    """Enrich r2_ready folder with metadata and covers"""
    print(f"\n{'='*70}")
    print("📦 ENRICHING R2_READY FOLDER")
    print(f"{'='*70}\n")
    
    # Map existing drama folders to book IDs
    drama_folders = [f for f in R2_READY_DIR.iterdir() if f.is_dir()]
    
    for folder in drama_folders:
        # Extract ID from folder name (drama_051678 -> 31001051678)
        match = re.search(r'drama_(\d+)', folder.name)
        if not match:
            continue
        
        short_id = match.group(1)
        
        # Find matching book ID
        book_id = None
        for bid in dramas_metadata.keys():
            if bid.endswith(short_id):
                book_id = bid
                break
        
        if not book_id:
            print(f"⚠️  {folder.name}: No metadata found, skipping...")
            continue
        
        print(f"\n📁 {folder.name}")
        print(f"   BookID: {book_id}")
        
        metadata = dramas_metadata[book_id]
        
        # Update metadata.json
        metadata_file = folder / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                existing_meta = json.load(f)
            
            # Enrich with new data
            existing_meta.update({
                'bookId': book_id,
                'title': metadata['title'],
                'description': metadata['description'],
                'genre': metadata['genre'],
                'tags': metadata['tags'],
                'totalEpisodes': metadata['totalEpisodes'],
                'author': metadata['author'],
                'coverUrl': metadata['coverUrl'],
            })
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(existing_meta, f, indent=2, ensure_ascii=False)
            
            print(f"   ✅ Updated metadata.json")
            print(f"      Title: {metadata['title']}")
            print(f"      Genre: {metadata['genre']}")
        
        # Download cover if not exists
        cover_file = folder / "cover.jpg"
        if not cover_file.exists() and metadata.get('coverUrl'):
            download_cover(metadata['coverUrl'], cover_file)

def main():
    print("\n" + "="*70)
    print("🔍 EXTRACT METADATA FROM HAR FILE")
    print("="*70)
    
    if not HAR_FILE.exists():
        print(f"\n❌ HAR file not found: {HAR_FILE}")
        print("   Please ensure HTTPToolkit HAR export exists.")
        return
    
    if not R2_READY_DIR.exists():
        print(f"\n❌ r2_ready directory not found: {R2_READY_DIR}")
        return
    
    # Extract metadata from HAR
    dramas_metadata = extract_metadata_from_har(HAR_FILE)
    
    if not dramas_metadata:
        print("\n⚠️  No drama metadata found in HAR file!")
        return
    
    print(f"\n✅ Extracted metadata for {len(dramas_metadata)} dramas")
    
    # Enrich r2_ready folder
    enrich_r2_ready(dramas_metadata)
    
    # Summary
    print(f"\n{'='*70}")
    print("✅ ENRICHMENT COMPLETE!")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
