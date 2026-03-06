#!/usr/bin/env python3
"""
Extract and Enrich Metadata from Frida Captures

This script:
1. Reads captured metadata from Frida (extended_capture.json, complete_capture.json)
2. Extracts drama info from API responses
3. Enriches books_metadata.json with real titles, covers, descriptions
4. Creates proper structure

Usage:
    python enrich_metadata_from_captures.py
"""

import json
import os
import re
import requests
from pathlib import Path
from typing import Dict, List, Any

# Paths
SCRIPT_DIR = Path(__file__).parent
SCRAPED_DATA_DIR = SCRIPT_DIR / "scraped_data"
OUTPUT_DIR = SCRIPT_DIR / "output"
METADATA_DIR = OUTPUT_DIR / "metadata"
COVERS_DIR = OUTPUT_DIR / "covers"

# Ensure dirs
METADATA_DIR.mkdir(parents=True, exist_ok=True)
COVERS_DIR.mkdir(parents=True, exist_ok=True)


def extract_metadata_from_captures() -> Dict[str, Any]:
    """Extract drama metadata from all capture files."""
    
    print(f"\n{'='*60}")
    print("📚 Extracting Metadata from Frida Captures")
    print(f"{'='*60}\n")
    
    metadata_by_book = {}
    
    # Try to load various capture files
    capture_files = [
        SCRAPED_DATA_DIR / "complete_capture.json",
        SCRAPED_DATA_DIR / "extended_capture.json",
        SCRAPED_DATA_DIR / "fresh_capture.json"
    ]
    
    for capture_file in capture_files:
        if not capture_file.exists():
            continue
        
        print(f"📂 Reading: {capture_file.name}")
        
        with open(capture_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different data structures
        if isinstance(data, list):
            # Data is a list of responses
            raw_responses = data
        elif isinstance(data, dict):
            # Data is a dict, check for rawApiResponses or videoUrls
            raw_responses = data.get('rawApiResponses', [])
            
            # If no rawApiResponses, try to extract book IDs from videoUrls
            if not raw_responses:
                video_urls = data.get('videoUrls', [])
                if video_urls:
                    print(f"  📹 Found {len(video_urls)} video URLs, extracting book IDs...")
                    
                    # Extract unique book IDs
                    book_ids = set()
                    for url_obj in video_urls:
                        book_id = url_obj.get('bookId')
                        if book_id:
                            book_ids.add(book_id)
                    
                    # Create placeholder metadata for these books
                    for book_id in book_ids:
                        if book_id not in metadata_by_book:
                            metadata_by_book[book_id] = {
                                'bookId': book_id,
                                'title': None,
                                'cover': None,
                                'description': None,
                                'source': 'goodshort',
                                'needsMetadata': True,
                                'capturedFrom': f"{capture_file.name} (videoUrls)"
                            }
                            print(f"  ⏳ Placeholder: {book_id} (needs metadata)")
                
                continue  # Skip to next file
        else:
            print(f"  ⚠️  Unknown data structure in {capture_file.name}")
            continue
        
        for response in raw_responses:
            url = response.get('url', '')
            body = response.get('body', '')
            
            if not body:
                continue
            
            try:
                # Parse response body
                response_data = json.loads(body)
                
                # Skip non-data responses
                if 'data' not in response_data:
                    continue
                
                api_data = response_data['data']
                
                # Check if it's book/drama metadata
                if isinstance(api_data, dict):
                    book_id = str(api_data.get('id') or api_data.get('bookId') or api_data.get('book_id') or '')
                    
                    # Only process if looks like a book ID (11 digits)
                    if book_id and len(book_id) >= 10 and book_id.isdigit():
                        
                        # Extract metadata
                        metadata = {
                            'bookId': book_id,
                            'title': api_data.get('title') or api_data.get('name') or api_data.get('bookName'),
                            'cover': api_data.get('cover') or api_data.get('coverUrl') or api_data.get('image'),
                            'coverHQ': api_data.get('coverHQ') or api_data.get('cover'),
                            'description': api_data.get('description') or api_data.get('desc') or api_data.get('synopsis') or api_data.get('intro'),
                            'author': api_data.get('author') or api_data.get('authorName'),
                            'category': api_data.get('category') or api_data.get('categoryName'),
                            'genre': api_data.get('genre') or api_data.get('category'),
                            'tags': api_data.get('tags') or api_data.get('tagList') or [],
                            'totalChapters': api_data.get('totalChapter') or api_data.get('chapterCount') or api_data.get('episodeCount') or 0,
                            'language': api_data.get('language') or 'id',
                            'rating': api_data.get('rating') or api_data.get('score'),
                            'views': api_data.get('viewCount') or api_data.get('views'),
                            'status': api_data.get('status'),
                            'source': 'goodshort',
                            'capturedFrom': capture_file.name
                        }
                        
                        # Only add if has title (real metadata)
                        if metadata['title']:
                            metadata_by_book[book_id] = metadata
                            print(f"  ✅ {metadata['title']} ({book_id})")
                
                # Check if it's a list of books
                elif isinstance(api_data, list) and len(api_data) > 0:
                    first_item = api_data[0]
                    
                    # Check if it's a book list
                    if 'bookId' in first_item or 'id' in first_item:
                        print(f"  📋 Found list with {len(api_data)} items")
                        
                        for item in api_data:
                            book_id = str(item.get('bookId') or item.get('id') or '')
                            
                            if book_id and len(book_id) >= 10:
                                # Partial metadata from list
                                if book_id not in metadata_by_book or not metadata_by_book[book_id].get('title'):
                                    metadata = {
                                        'bookId': book_id,
                                        'title': item.get('title') or item.get('name') or item.get('bookName'),
                                        'cover': item.get('cover') or item.get('coverUrl'),
                                        'description': item.get('description') or item.get('desc'),
                                        'category': item.get('category') or item.get('categoryName'),
                                        'totalChapters': item.get('totalChapter') or item.get('chapterCount') or 0,
                                        'source': 'goodshort',
                                        'capturedFrom': f"{capture_file.name} (list)"
                                    }
                                    
                                    if metadata['title']:
                                        metadata_by_book[book_id] = metadata
                
            except json.JSONDecodeError:
                continue
            except Exception as e:
                # print(f"  ⚠️  Error parsing response: {e}")
                continue
    
    # Also check books_metadata.json for existing data
    books_meta_file = SCRAPED_DATA_DIR / "books_metadata.json"
    if books_meta_file.exists():
        with open(books_meta_file, 'r', encoding='utf-8') as f:
            existing = json.load(f)
        
        for book_id, data in existing.items():
            if book_id not in metadata_by_book:
                metadata_by_book[book_id] = data
    
    print(f"\n✅ Extracted metadata for {len(metadata_by_book)} dramas\n")
    return metadata_by_book


def download_cover(url: str, book_id: str) -> str:
    """Download cover image."""
    if not url:
        return ''
    
    try:
        ext = 'jpg' if '.jpg' in url else 'png'
        output_path = COVERS_DIR / f"{book_id}.{ext}"
        
        if output_path.exists():
            return str(output_path)
        
        print(f"  📥 Downloading cover for {book_id}...")
        
        response = requests.get(url, headers={'User-Agent': 'okhttp/4.9.3'}, timeout=30)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        print(f"  ✅ Saved: {output_path.name}")
        return str(output_path)
        
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        return ''


def main():
    print(f"\n{'='*60}")
    print("🔍 GoodShort Metadata Enrichment")
    print(f"{'='*60}\n")
    
    # Extract metadata
    metadata_by_book = extract_metadata_from_captures()
    
    if not metadata_by_book:
        print("❌ No metadata found in capture files!")
        print("\nTo get metadata:")
        print("  1. Run: start-capture-enhanced.bat")
        print("  2. Browse dramas in the app")
        print("  3. Type: save() in Frida console")
        print("  4. Save output to scraped_data/metadata_complete.json")
        return
    
    # Download covers
    print("📥 Downloading covers...\n")
    for book_id, metadata in metadata_by_book.items():
        if metadata.get('cover'):
            cover_path = download_cover(metadata['cover'], book_id)
            if cover_path:
                metadata['coverLocal'] = cover_path
    
    # Save enriched metadata
    output_file = SCRAPED_DATA_DIR / "books_metadata_enriched.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(metadata_by_book, f, indent=2, ensure_ascii=False)
    
    # Also save individual files
    for book_id, metadata in metadata_by_book.items():
        individual_file = METADATA_DIR / f"{book_id}.json"
        with open(individual_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print("✅ ENRICHMENT COMPLETE")
    print(f"{'='*60}")
    print(f"\nProcessed: {len(metadata_by_book)} dramas")
    print(f"Output:    {output_file}")
    print(f"Metadata:  {METADATA_DIR}")
    print(f"Covers:    {COVERS_DIR}")
    
    # Summary
    print(f"\n📊 Summary:")
    for book_id, meta in metadata_by_book.items():
        title = meta.get('title') or f"Drama {book_id}"
        chapters = meta.get('totalChapters') or '?'
        category = meta.get('category') or 'Unknown'
        print(f"  • {title} ({book_id}) - {chapters} eps - {category}")
    
    print()


if __name__ == "__main__":
    main()
