#!/usr/bin/env python3
"""Quick test script to validate HAR file structure before batch processing"""

import json
import sys
from pathlib import Path

def validate_har_file(har_path: Path):
    """Quick validation of HAR file"""
    
    print(f"\n{'='*70}")
    print(f"🔍 Validating HAR File: {har_path.name}")
    print(f"{'='*70}\n")
    
    if not har_path.exists():
        print(f"❌ File not found: {har_path}")
        return False
    
    # Check file size
    size_mb = har_path.stat().st_size / (1024 * 1024)
    print(f"📁 File size: {size_mb:.2f} MB")
    
    # Parse HAR
    try:
        with open(har_path, 'r', encoding='utf-8') as f:
            har_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return False
    
    # Count entries
    entries = har_data.get('log', {}).get('entries', [])
    print(f"📊 Total HTTP requests: {len(entries)}")
    
    # Look for GoodShort API calls
    book_info_calls = 0
    chapter_list_calls = 0
    video_urls = 0
    
    for entry in entries:
        url = entry['request']['url']
        
        if 'getBookInfo' in url:
            book_info_calls += 1
        elif 'getChapterList' in url:
            chapter_list_calls += 1
        
        # Check for video URLs in responses
        response = entry.get('response', {})
        content = response.get('content', {})
        text = content.get('text', '')
        
        if 'videoUrl' in text and 'https' in text:
            video_urls += 1
    
    print(f"\n📈 GoodShort API Calls:")
    print(f"   - Book Info (drama metadata): {book_info_calls}")
    print(f"   - Chapter Lists (episodes): {chapter_list_calls}")
    print(f"   - Video URLs found: {video_urls}")
    
    # Estimate dramas
    estimated_dramas = min(book_info_calls, chapter_list_calls)
    print(f"\n🎬 Estimated dramas captured: {estimated_dramas}")
    
    if estimated_dramas == 0:
        print(f"\n⚠️  WARNING: No drama data found in HAR file!")
        print(f"   Make sure you:")
        print(f"   1. Opened drama detail pages in GoodShort app")
        print(f"   2. Scrolled through episode lists")
        print(f"   3. Played at least 1 episode per drama")
        return False
    
    if estimated_dramas < 5:
        print(f"\n⚠️  WARNING: Only {estimated_dramas} dramas found")
        print(f"   Consider capturing more dramas in this session")
    
    print(f"\n✅ HAR file looks good!")
    print(f"   Ready to process with batch_har_processor.py")
    
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_har.py <har_file>")
        sys.exit(1)
    
    har_file = Path(sys.argv[1])
    validate_har_file(har_file)
