#!/usr/bin/env python3
"""
GoodShort Data Processor - Process mitmproxy capture data
Downloads covers, organizes videos, prepares for R2 upload

Usage: python process_mitm_data.py
"""

import json
import os
import re
import time
import requests
import subprocess
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

# Paths
SCRIPT_DIR = Path(__file__).parent
CAPTURE_DIR = SCRIPT_DIR / "mitm_capture"
OUTPUT_DIR = SCRIPT_DIR / "r2_ready"

# Create dirs
OUTPUT_DIR.mkdir(exist_ok=True)

# Rate limiting
RATE_LIMIT = 0.3  # seconds between requests

def load_capture_data():
    """Load captured data from mitmproxy"""
    data_file = CAPTURE_DIR / "goodshort_data.json"
    
    if not data_file.exists():
        print("❌ No capture data found!")
        print(f"   Expected: {data_file}")
        print()
        print("Run mitmproxy first:")
        print("  mitmdump -s goodshort_mitmproxy.py -p 8888")
        return None
    
    with open(data_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_slug(title: str) -> str:
    """Create URL-safe folder name from title"""
    slug = title.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '_', slug)
    slug = slug.strip('_')
    return slug[:50]  # Limit length


def download_file(url: str, dest: Path, retries: int = 3) -> bool:
    """Download file with retries"""
    for attempt in range(retries):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36',
                'Accept': '*/*',
                'Referer': 'https://goodreels.com/'
            }
            
            resp = requests.get(url, headers=headers, timeout=30, stream=True)
            resp.raise_for_status()
            
            with open(dest, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return True
            
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1)
                continue
            print(f"      ❌ Failed: {str(e)[:50]}")
            return False
    
    return False


def download_video_segments(video_urls: list, output_file: Path) -> bool:
    """Download and combine video segments into MP4"""
    if not video_urls:
        return False
    
    temp_dir = output_file.parent / f"temp_{output_file.stem}"
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # Sort URLs by segment number
        def get_segment_num(url):
            match = re.search(r'_(\d+)\.ts', url)
            return int(match.group(1)) if match else 0
        
        sorted_urls = sorted(video_urls, key=get_segment_num)
        
        # Download segments
        segment_files = []
        for i, url in enumerate(sorted_urls):
            seg_file = temp_dir / f"seg_{i:04d}.ts"
            
            if download_file(url, seg_file):
                segment_files.append(seg_file)
            
            time.sleep(RATE_LIMIT)
        
        if not segment_files:
            return False
        
        # Create concat list
        list_file = temp_dir / "concat.txt"
        with open(list_file, 'w') as f:
            for seg in segment_files:
                f.write(f"file '{seg.name}'\n")
        
        # Combine with ffmpeg
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(list_file),
            '-c', 'copy',
            str(output_file)
        ]
        
        result = subprocess.run(cmd, capture_output=True, cwd=temp_dir)
        
        if result.returncode == 0 and output_file.exists():
            # Cleanup temp
            for f in temp_dir.iterdir():
                f.unlink()
            temp_dir.rmdir()
            return True
        else:
            print(f"      ffmpeg error: {result.stderr.decode()[:100]}")
            return False
            
    except Exception as e:
        print(f"      Error: {e}")
        return False


def process_drama(book_id: str, drama: dict, episodes: list, video_urls: list, cover_url: str):
    """Process a single drama - download cover and videos"""
    title = drama.get('title') or f"Drama_{book_id}"
    slug = create_slug(title)
    
    drama_dir = OUTPUT_DIR / slug
    drama_dir.mkdir(exist_ok=True)
    
    episodes_dir = drama_dir / "episodes"
    episodes_dir.mkdir(exist_ok=True)
    
    print(f"\n📁 Processing: {title}")
    print(f"   ID: {book_id}")
    
    # Build chapter_id to sequence mapping from episode list
    chapter_to_seq = {}
    for ep in episodes:
        ch_id = str(ep.get('chapter_id', ''))
        seq = ep.get('sequence', 0)
        if ch_id:
            chapter_to_seq[ch_id] = seq
    
    print(f"   Episodes in API: {len(episodes)}")
    print(f"   Video URLs captured: {len(video_urls)}")
    
    # Download cover
    cover_file = drama_dir / "cover.jpg"
    actual_cover_url = cover_url or drama.get('cover_url', '')
    
    if actual_cover_url:
        # Ensure full URL
        if not actual_cover_url.startswith('http'):
            actual_cover_url = f"https://acf.goodreels.com/{actual_cover_url}"
        
        print(f"   📷 Downloading cover...", end=' ', flush=True)
        if download_file(actual_cover_url, cover_file):
            print("✅")
        else:
            print("❌")
        
        time.sleep(RATE_LIMIT)
    
    # Group video URLs by chapter_id
    videos_by_chapter = defaultdict(list)
    for v in video_urls:
        ch_id = str(v.get('chapter_id', ''))
        if ch_id:
            videos_by_chapter[ch_id].append(v['url'])
    
    print(f"   📹 Video chapters found: {len(videos_by_chapter)}")
    
    # Download videos with correct episode numbering
    episodes_processed = []
    
    for chapter_id, segment_urls in videos_by_chapter.items():
        # Get episode number from chapter list
        episode_num = chapter_to_seq.get(chapter_id)
        
        if episode_num is None:
            # Try to infer from order of appearance
            episode_num = len(episodes_processed) + 1
            print(f"      ⚠️ Chapter {chapter_id} not in episode list, using position {episode_num}")
        
        episode_file = episodes_dir / f"episode_{episode_num:03d}.mp4"
        
        print(f"      Episode {episode_num} ({len(segment_urls)} segments)...", end=' ', flush=True)
        
        if download_video_segments(segment_urls, episode_file):
            file_size = episode_file.stat().st_size / (1024 * 1024)
            print(f"✅ ({file_size:.1f} MB)")
            
            episodes_processed.append({
                "number": episode_num,
                "chapter_id": chapter_id,
                "filename": episode_file.name,
                "size_mb": file_size
            })
        else:
            print("❌")
    
    # Sort episodes by number
    episodes_processed.sort(key=lambda x: x['number'])
    
    # Create metadata
    metadata = {
        "drama_id": book_id,
        "title": title,
        "slug": slug,
        "author": drama.get('author', ''),
        "description": drama.get('description', ''),
        "genre": drama.get('genre', ''),
        "cover_url": actual_cover_url,
        "cover_file": "cover.jpg" if cover_file.exists() else None,
        "language": drama.get('language', 'Indonesian'),
        "chapter_count": drama.get('chapter_count', 0),
        "view_count": drama.get('view_count', 0),
        "rating": drama.get('rating', 0),
        "status": drama.get('status', ''),
        "episodes_available": len(episodes_processed),
        "episodes": episodes_processed,
        "total_size_mb": sum(ep['size_mb'] for ep in episodes_processed),
        "processed_at": datetime.now().isoformat()
    }
    
    metadata_file = drama_dir / "metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"   ✅ Saved: {len(episodes_processed)} episodes, {metadata['total_size_mb']:.1f} MB")
    
    return metadata


def main():
    print()
    print("=" * 70)
    print("🎬 GoodShort Data Processor - FINAL SOLUTION")
    print("=" * 70)
    print()
    
    # Load data
    data = load_capture_data()
    if not data:
        return
    
    print(f"📊 Capture Summary:")
    print(f"   Dramas: {data['stats']['dramas']}")
    print(f"   Episodes: {data['stats']['episodes']}")
    print(f"   Video URLs: {data['stats']['video_urls']}")
    print(f"   Covers: {data['stats']['covers']}")
    print()
    
    dramas = data.get('dramas', {})
    episodes = data.get('episodes', {})
    video_urls = data.get('video_urls', {})
    covers = data.get('covers', {})
    
    if not dramas:
        print("❌ No dramas found in capture data!")
        return
    
    # Process each drama
    all_metadata = []
    
    for book_id, drama in dramas.items():
        drama_episodes = episodes.get(book_id, [])
        drama_videos = video_urls.get(book_id, [])
        drama_cover = covers.get(book_id, '')
        
        if not drama_videos:
            print(f"\n⏩ Skipping {drama.get('title', book_id)} (no video URLs)")
            continue
        
        metadata = process_drama(book_id, drama, drama_episodes, drama_videos, drama_cover)
        all_metadata.append(metadata)
    
    # Create manifest
    if all_metadata:
        manifest = {
            "created": datetime.now().strftime("%Y-%m-%d"),
            "total_dramas": len(all_metadata),
            "total_episodes": sum(m['episodes_available'] for m in all_metadata),
            "total_size_mb": sum(m['total_size_mb'] for m in all_metadata),
            "dramas": [
                {
                    "id": m['drama_id'],
                    "title": m['title'],
                    "folder": m['slug'],
                    "episodes": m['episodes_available'],
                    "size_mb": m['total_size_mb']
                }
                for m in all_metadata
            ]
        }
        
        manifest_file = OUTPUT_DIR / "r2_manifest.json"
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        print()
        print("=" * 70)
        print("✅ PROCESSING COMPLETE!")
        print("=" * 70)
        print(f"\n📊 Total:")
        print(f"   Dramas: {manifest['total_dramas']}")
        print(f"   Episodes: {manifest['total_episodes']}")
        print(f"   Size: {manifest['total_size_mb']:.1f} MB")
        print(f"\n📁 Output: {OUTPUT_DIR}")
        print(f"\n🚀 Next step: python upload_r2_ready.py")
    else:
        print("\n❌ No dramas processed!")


if __name__ == "__main__":
    main()
