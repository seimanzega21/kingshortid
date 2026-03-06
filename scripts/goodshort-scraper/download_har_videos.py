#!/usr/bin/env python3
"""
Download videos from HAR analysis with CORRECT episode ordering.
Groups segments by folder_hash, determines episode order by capture time.
"""

import json
import os
import re
import time
import requests
import subprocess
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Paths
SCRIPT_DIR = Path(__file__).parent
ANALYSIS_DIR = SCRIPT_DIR / "fresh_capture_analysis"
OUTPUT_DIR = SCRIPT_DIR / "r2_ready"

# Rate limiting
RATE_LIMIT = 0.2

def load_data():
    """Load video segments and metadata from analysis"""
    segments_file = ANALYSIS_DIR / "video_segments.json"
    api_file = ANALYSIS_DIR / "all_api_calls.json"
    
    with open(segments_file, 'r', encoding='utf-8') as f:
        segments = json.load(f)
    
    # Load API data for metadata
    metadata = {}
    try:
        with open(api_file, 'r', encoding='utf-8') as f:
            api_data = json.load(f)
        
        for call in api_data:
            url = call.get('url', '')
            data = call.get('data', {})
            
            if '/book/details' in url or '/book/info' in url:
                book_data = data.get('data', {})
                if 'book' in book_data:
                    book_data = book_data['book']
                
                book_id = str(book_data.get('bookId') or book_data.get('id') or '')
                if book_id:
                    metadata[book_id] = {
                        'title': book_data.get('bookName') or book_data.get('name') or f'Drama_{book_id}',
                        'description': book_data.get('introduction') or book_data.get('desc') or '',
                        'cover': book_data.get('cover') or book_data.get('coverImg') or '',
                        'genre': book_data.get('genreName') or book_data.get('category') or '',
                        'author': book_data.get('pseudonym') or book_data.get('author') or ''
                    }
    except Exception as e:
        print(f"Warning: Could not load API data: {e}")
    
    return segments, metadata


def group_by_episode(segment_urls):
    """Group segments by folder_hash (unique per episode)"""
    episodes = defaultdict(list)
    
    for url in segment_urls:
        # Extract folder_hash from URL
        # Pattern: /mts/books/{x}/{bookId}/{chapterId}/{folder_hash}/{resolution}/{filename}.ts
        match = re.search(r'/(\w{10})/720p/\w+_720p_(\d+)\.ts', url)
        if match:
            folder_hash = match.group(1)
            segment_num = int(match.group(2))
            episodes[folder_hash].append((segment_num, url))
    
    # Sort each episode's segments by segment number
    for folder_hash in episodes:
        episodes[folder_hash].sort(key=lambda x: x[0])
    
    return dict(episodes)


def download_segment(url: str, dest: Path) -> bool:
    """Download a single segment"""
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
        print(f"      Error: {str(e)[:50]}")
        return False


def combine_to_mp4(segment_files: list, output_file: Path) -> bool:
    """Combine .ts segments to .mp4 using ffmpeg"""
    if not segment_files:
        return False
    
    temp_dir = output_file.parent / f"temp_{output_file.stem}"
    temp_dir.mkdir(exist_ok=True)
    
    # Create concat list
    list_file = temp_dir / "concat.txt"
    with open(list_file, 'w') as f:
        for seg in segment_files:
            f.write(f"file '{seg.absolute()}'\n")
    
    cmd = [
        'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
        '-i', str(list_file), '-c', 'copy', str(output_file)
    ]
    
    result = subprocess.run(cmd, capture_output=True)
    
    # Cleanup
    try:
        list_file.unlink()
        temp_dir.rmdir()
    except:
        pass
    
    return result.returncode == 0


def create_slug(title: str) -> str:
    """Create URL-safe folder name"""
    slug = title.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '_', slug)
    return slug[:50].strip('_')


def process_drama(drama_key: str, segment_urls: list, metadata: dict):
    """Process a single drama - download and organize episodes"""
    # Extract IDs from key (format: "xxx_bookId")
    parts = drama_key.split('_')
    book_id = parts[1] if len(parts) > 1 else parts[0]
    
    # Get metadata
    meta = metadata.get(book_id, {})
    title = meta.get('title', f'Drama_{book_id}')
    slug = create_slug(title)
    
    print(f"\n{'='*60}")
    print(f"Processing: {title}")
    print(f"Book ID: {book_id}")
    print(f"Total segments: {len(segment_urls)}")
    
    # Group by episode (folder_hash)
    episodes = group_by_episode(segment_urls)
    print(f"Episodes detected: {len(episodes)}")
    
    # Create output directory
    drama_dir = OUTPUT_DIR / slug
    episodes_dir = drama_dir / "episodes"
    episodes_dir.mkdir(parents=True, exist_ok=True)
    temp_dir = drama_dir / "temp_segments"
    temp_dir.mkdir(exist_ok=True)
    
    # Process each episode
    processed_episodes = []
    
    for ep_num, (folder_hash, segments) in enumerate(episodes.items(), 1):
        print(f"\n  Episode {ep_num} ({folder_hash}): {len(segments)} segments")
        
        # Download segments
        downloaded = []
        for seg_num, url in segments:
            seg_file = temp_dir / f"ep{ep_num:03d}_seg{seg_num:06d}.ts"
            
            if seg_file.exists():
                downloaded.append(seg_file)
                continue
            
            print(f"    Downloading segment {seg_num}...", end=' ', flush=True)
            if download_segment(url, seg_file):
                downloaded.append(seg_file)
                print("OK")
            else:
                print("FAIL")
            
            time.sleep(RATE_LIMIT)
        
        # Combine to MP4
        if downloaded:
            output_file = episodes_dir / f"episode_{ep_num:03d}.mp4"
            print(f"    Combining to {output_file.name}...", end=' ', flush=True)
            
            if combine_to_mp4(downloaded, output_file):
                size_mb = output_file.stat().st_size / (1024 * 1024)
                print(f"OK ({size_mb:.1f} MB)")
                
                processed_episodes.append({
                    'number': ep_num,
                    'folder_hash': folder_hash,
                    'filename': output_file.name,
                    'size_mb': round(size_mb, 2)
                })
                
                # Cleanup segments
                for seg in downloaded:
                    try:
                        seg.unlink()
                    except:
                        pass
            else:
                print("FAIL")
    
    # Cleanup temp dir
    try:
        temp_dir.rmdir()
    except:
        pass
    
    # Download cover
    cover_url = meta.get('cover', '')
    if cover_url:
        if not cover_url.startswith('http'):
            cover_url = f"https://acf.goodreels.com/{cover_url}"
        
        cover_file = drama_dir / "cover.jpg"
        print(f"\n  Downloading cover...", end=' ', flush=True)
        if download_segment(cover_url, cover_file):
            print("OK")
        else:
            print("FAIL")
    
    # Save metadata
    final_meta = {
        'drama_id': book_id,
        'title': title,
        'slug': slug,
        'description': meta.get('description', ''),
        'genre': meta.get('genre', ''),
        'author': meta.get('author', ''),
        'episodes_count': len(processed_episodes),
        'episodes': processed_episodes,
        'total_size_mb': round(sum(ep['size_mb'] for ep in processed_episodes), 2),
        'processed_at': datetime.now().isoformat()
    }
    
    meta_file = drama_dir / "metadata.json"
    with open(meta_file, 'w', encoding='utf-8') as f:
        json.dump(final_meta, f, indent=2, ensure_ascii=False)
    
    print(f"\n  DONE: {len(processed_episodes)} episodes, {final_meta['total_size_mb']:.1f} MB")
    
    return final_meta


def main():
    print("="*60)
    print("GoodShort Video Downloader - Episode Ordering Fix")
    print("="*60)
    
    # Load data
    segments, metadata = load_data()
    print(f"\nFound {len(segments)} dramas to process")
    print(f"Metadata available for: {list(metadata.keys())}")
    
    # Process each drama
    all_results = []
    for drama_key, urls in segments.items():
        result = process_drama(drama_key, urls, metadata)
        all_results.append(result)
    
    # Save manifest
    manifest = {
        'created': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'total_dramas': len(all_results),
        'total_episodes': sum(r['episodes_count'] for r in all_results),
        'total_size_mb': round(sum(r['total_size_mb'] for r in all_results), 2),
        'dramas': [
            {
                'id': r['drama_id'],
                'title': r['title'],
                'folder': r['slug'],
                'episodes': r['episodes_count'],
                'size_mb': r['total_size_mb']
            }
            for r in all_results
        ]
    }
    
    manifest_file = OUTPUT_DIR / "r2_manifest.json"
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    print("\n" + "="*60)
    print("COMPLETE!")
    print("="*60)
    print(f"Dramas: {manifest['total_dramas']}")
    print(f"Episodes: {manifest['total_episodes']}")
    print(f"Total Size: {manifest['total_size_mb']:.1f} MB")
    print(f"\nOutput: {OUTPUT_DIR}")
    print(f"\nNext: python upload_r2_ready.py")


if __name__ == "__main__":
    main()
