#!/usr/bin/env python3
"""
Production Metadata Processor

Processes Frida capture data and generates production-ready metadata:
1. Download all real covers from GoodShort CDN
2. Generate complete metadata JSON
3. Organize files for import to database
4. Validate data completeness

Usage:
    python production_processor.py
"""

import json
import requests
from pathlib import Path
from typing import Dict, List, Any
import time
from urllib.parse import urlparse

# Paths
SCRIPT_DIR = Path(__file__).parent
FRIDA_OUTPUT = SCRIPT_DIR / "goodshort_production_data.json"
TOKEN_CONFIG = SCRIPT_DIR / "goodshort_tokens.json"
OUTPUT_DIR = SCRIPT_DIR / "production_output"
COVERS_DIR = OUTPUT_DIR / "covers"
METADATA_FILE = OUTPUT_DIR / "final_metadata.json"
IMPORT_SCRIPT = OUTPUT_DIR / "database_import.sql"

# Ensure directories
COVERS_DIR.mkdir(parents=True, exist_ok=True)

# Rate limiting
RATE_LIMIT_DELAY = 0.5  # seconds between requests


def load_frida_data() -> Dict[str, Any]:
    """Load data from Frida capture."""
    print("📂 Loading Frida capture data...")
    
    if not FRIDA_OUTPUT.exists():
        print("❌ Frida output not found!")
        print(f"   Expected: {FRIDA_OUTPUT}")
        print("\n💡 Run this first:")
        print("   1. adb pull /sdcard/goodshort_production_data.json .")
        print("   2. Move to script directory")
        return None
    
    with open(FRIDA_OUTPUT, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✅ Loaded {len(data.get('dramas', {}))} dramas")
    return data


def load_tokens() -> Dict[str, Any]:
    """Load authentication tokens if available."""
    if TOKEN_CONFIG.exists():
        with open(TOKEN_CONFIG, 'r') as f:
            return json.load(f)
    return {}


def download_cover(url: str, book_id: str) -> Path | None:
    """Download cover image from CDN."""
    if not url:
        return None
    
    try:
        # Clean URL
        clean_url = url.split('?')[0] if '?' in url else url
        
        # Determine file extension
        ext = Path(urlparse(clean_url).path).suffix or '.jpg'
        output_path = COVERS_DIR / f"{book_id}{ext}"
        
        # Skip if already exists
        if output_path.exists():
            print(f"   ⏭️  Already have: {book_id}")
            return output_path
        
        # Download
        headers = {
            'User-Agent': 'GoodReels/1.0',
            'Accept': 'image/*'
        }
        
        response = requests.get(clean_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Save
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        print(f"   ✅ Downloaded: {book_id} ({len(response.content) // 1024} KB)")
        
        # Rate limiting
        time.sleep(RATE_LIMIT_DELAY)
        
        return output_path
        
    except Exception as e:
        print(f"   ❌ Failed {book_id}: {e}")
        return None


def process_dramas(frida_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process all dramas and generate production metadata."""
    dramas = frida_data.get('dramas', {})
    covers_map = frida_data.get('covers', {})
    
    print(f"\n{'='*80}")
    print("🎬 Processing Dramas")
    print(f"{'='*80}\n")
    
    final_metadata = {}
    stats = {
        'total': len(dramas),
        'complete': 0,
        'covers_downloaded': 0,
        'missing_title': 0,
        'missing_cover': 0
    }
    
    for book_id, drama in dramas.items():
        print(f"\n📚 {book_id}: {drama.get('title') or 'Untitled'}")
        
        # Determine best cover URL
        cover_url = None
        if drama.get('coverHQ'):
            cover_url = drama['coverHQ']
        elif drama.get('cover'):
            cover_url = drama['cover']
        elif book_id in covers_map:
            # Pick largest available
            sizes = covers_map[book_id]
            for size_key in ['1080', '720', 'large', 'medium']:
                for key, url in sizes.items():
                    if size_key in key:
                        cover_url = url
                        break
                if cover_url:
                    break
            
            # Fallback to any available
            if not cover_url and sizes:
                cover_url = list(sizes.values())[0]
        
        # Download cover
        cover_path = None
        if cover_url:
            cover_path = download_cover(cover_url, book_id)
            if cover_path:
                stats['covers_downloaded'] += 1
        else:
            stats['missing_cover'] += 1
            print(f"   ⚠️  No cover URL found")
        
        # Build production metadata
        metadata = {
            "bookId": book_id,
            "sourceId": book_id,
            "source": "goodshort",
            
            # Core info
            "title": drama.get('title') or f"Drama Indonesia #{book_id[-3:]}",
            "originalTitle": drama.get('originalTitle'),
            "alternativeTitle": "Indonesian Short Drama",
            
            # Description
            "description": drama.get('description') or "Drama pendek Indonesia dengan cerita menarik dan emosional.",
            
            # Cover
            "cover": f"/api/covers/{book_id}.jpg" if cover_path else None,
            "coverLocal": str(cover_path) if cover_path else None,
            "coverOptions": drama.get('coverOptions', {}),
            
            # Classification
            "genre": drama.get('genre') or "Drama",
            "category": drama.get('category') or "Drama Indonesia",
            "tags": drama.get('tags', []) or ["Drama Indonesia", "Short Drama"],
            
            # Metadata
            "author": drama.get('author'),
            "language": drama.get('metadata', {}).get('language') or "id",
            "country": "Indonesia",
            
            # Stats
            "totalEpisodes": len(drama.get('episodes', [])) or drama.get('totalEpisodes', 0),
            "status": drama.get('metadata', {}).get('status') or "completed",
            "quality": "HD 720p",
            "duration": "Short Form (< 5 min per episode)",
            
            # Engagement
            "rating": drama.get('metadata', {}).get('rating') or 4.5,
            "views": drama.get('metadata', {}).get('views') or 0,
            "likes": drama.get('metadata', {}).get('likes') or 0,
            
            # Premium
            "isFree": True,
            "isPremium": False,
            
            # Episodes
            "episodes": [
                {
                    "episodeNumber": ep.get('order', idx + 1),
                    "chapterId": ep.get('id'),
                    "title": ep.get('title') or f"Episode {idx + 1}",
                    "description": f"Episode {idx + 1} dari {drama.get('title') or 'drama'}",
                    "duration": ep.get('duration') or 180,
                    "isFree": ep.get('isFree', True),
                    "thumbnail": ep.get('thumbnail'),
                    "videoUrl": f"/api/videos/{book_id}/episode-{idx + 1}.m3u8",
                    "thumbnailUrl": f"/api/thumbnails/{book_id}/episode-{idx + 1}.jpg"
                }
                for idx, ep in enumerate(drama.get('episodes', []))
            ],
            
            # Video URLs (for reference)
            "videoUrls": drama.get('videoUrls', []),
            
            # Production metadata
            "productionMetadata": {
                "capturedAt": drama.get('capturedAt'),
                "hasRealTitle": bool(drama.get('title')),
                "hasRealCover": bool(cover_url),
                "hasDescription": bool(drama.get('description')),
                "isComplete": bool(drama.get('title') and cover_url and drama.get('description')),
                "version": "5.0-production"
            }
        }
        
        # Check completeness
        if metadata['productionMetadata']['isComplete']:
            stats['complete'] += 1
            print(f"   ✅ COMPLETE")
        else:
            if not drama.get('title'):
                stats['missing_title'] += 1
                print(f"   ⚠️  Using placeholder title")
            if not cover_url:
                print(f"   ⚠️  Missing cover")
            if not drama.get('description'):
                print(f"   ⚠️  Using generic description")
        
        final_metadata[book_id] = metadata
    
    return final_metadata, stats


def generate_database_import(metadata: Dict[str, Any]) -> str:
    """Generate SQL import script for database."""
    sql_lines = [
        "-- GoodShort Drama Import Script",
        "-- Generated by Production Processor",
        f"-- Total dramas: {len(metadata)}",
        "",
        "BEGIN TRANSACTION;",
        ""
    ]
    
    for book_id, drama in metadata.items():
        # Escape single quotes
        title = drama['title'].replace("'", "''")
        desc = drama['description'].replace("'", "''")
        
        sql = f"""
INSERT INTO dramas (
    source_id, source, title, description, cover, genre, category,
    language, country, total_episodes, status, quality, rating, views,
    is_free, is_premium, metadata, created_at
) VALUES (
    '{book_id}',
    'goodshort',
    '{title}',
    '{desc}',
    '{drama["cover"]}',
    '{drama["genre"]}',
    '{drama["category"]}',
    '{drama["language"]}',
    '{drama["country"]}',
    {drama["totalEpisodes"]},
    '{drama["status"]}',
    '{drama["quality"]}',
    {drama["rating"]},
    {drama["views"]},
    TRUE,
    FALSE,
    '{json.dumps(drama["productionMetadata"])}',
    NOW()
);
""".strip()
        
        sql_lines.append(sql)
        sql_lines.append("")
    
    sql_lines.append("COMMIT;")
    
    return "\n".join(sql_lines)


def main():
    print("\n" + "="*80)
    print("🚀 GoodShort Production Metadata Processor")
    print("="*80 + "\n")
    
    # Load Frida data
    frida_data = load_frida_data()
    if not frida_data:
        return
    
    # Load tokens (optional)
    tokens = load_tokens()
    if tokens:
        print(f"🔑 Loaded tokens: {list(tokens.keys())}")
    
    # Process dramas
    final_metadata, stats = process_dramas(frida_data)
    
    # Save metadata
    print(f"\n{'='*80}")
    print("💾 Saving Production Metadata")
    print(f"{'='*80}\n")
    
    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_metadata, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved: {METADATA_FILE}")
    print(f"   Size: {METADATA_FILE.stat().st_size // 1024} KB")
    
    # Generate SQL import
    sql = generate_database_import(final_metadata)
    with open(IMPORT_SCRIPT, 'w', encoding='utf-8') as f:
        f.write(sql)
    
    print(f"✅ Saved: {IMPORT_SCRIPT}")
    
    # Print summary
    print(f"\n{'='*80}")
    print("📊 PRODUCTION SUMMARY")
    print(f"{'='*80}\n")
    
    print(f"Total Dramas:       {stats['total']}")
    print(f"Complete Metadata:  {stats['complete']} ✅")
    print(f"Covers Downloaded:  {stats['covers_downloaded']}")
    print(f"Missing Titles:     {stats['missing_title']}")
    print(f"Missing Covers:     {stats['missing_cover']}")
    
    print(f"\n{'='*80}")
    print("✅ READY FOR PRODUCTION")
    print(f"{'='*80}\n")
    
    print("📁 Output:")
    print(f"   Metadata: {METADATA_FILE}")
    print(f"   Covers:   {COVERS_DIR}/ ({stats['covers_downloaded']} files)")
    print(f"   SQL:      {IMPORT_SCRIPT}")
    
    print("\n📋 Next Steps:")
    print("   1. Review metadata.json")
    print("   2. Copy covers to backend: cp production_output/covers/* /path/to/backend/public/covers/")
    print("   3. Import to database: psql -f production_output/database_import.sql")
    print("   4. Deploy!")
    print()


if __name__ == "__main__":
    main()
