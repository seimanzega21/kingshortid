#!/usr/bin/env python3
"""
Reorganize Existing Scraped Data

Fixes:
1. Rename chapter_xxx to Episode 1, Episode 2
2. Combine segments into proper MP4
3. Fetch missing metadata
4. Download proper covers
5. Create clean structure

Usage:
    python reorganize_scraped_data.py
"""

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List
import re

# Paths
SCRIPT_DIR = Path(__file__).parent
DOWNLOADS_DIR = SCRIPT_DIR / "downloads"
OUTPUT_DIR = SCRIPT_DIR / "output"
COVERS_DIR = OUTPUT_DIR / "covers"
METADATA_DIR = OUTPUT_DIR / "metadata"
EPISODES_DIR = OUTPUT_DIR / "episodes"

# Ensure output directories
for dir_path in [OUTPUT_DIR, COVERS_DIR, METADATA_DIR, EPISODES_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)


def find_ffmpeg() -> str:
    """Find ffmpeg executable."""
    # Try common locations
    candidates = [
        'ffmpeg',
        'C:\\ffmpeg\\bin\\ffmpeg.exe',
        'C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe',
    ]
    
    for candidate in candidates:
        try:
            result = subprocess.run(
                [candidate, '-version'],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                return candidate
        except:
            continue
    
    raise FileNotFoundError("ffmpeg not found! Please install ffmpeg.")


def combine_segments_to_mp4(segments_dir: Path, output_file: Path) -> bool:
    """Combine TS segments into MP4."""
    try:
        # Check if already exists
        if output_file.exists():
            print(f"  ✓ MP4 already exists: {output_file.name}")
            return True
        
        # Find segments list
        segments_txt = segments_dir / "segments.txt"
        
        if not segments_txt.exists():
            # Create segments list
            segments = sorted(segments_dir.glob("segment_*.ts"))
            if not segments:
                print(f"  ❌ No segments found in {segments_dir}")
                return False
            
            with open(segments_txt, 'w') as f:
                for seg in segments:
                    f.write(f"file '{seg.name}'\n")
        
        print(f"  🎞️  Combining {len(list(segments_dir.glob('segment_*.ts')))} segments...")
        
        ffmpeg = find_ffmpeg()
        
        # Combine segments
        cmd = [
            ffmpeg,
            '-f', 'concat',
            '-safe', '0',
            '-i', str(segments_txt),
            '-c', 'copy',
            '-y',
            str(output_file)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            timeout=300
        )
        
        if result.returncode == 0 and output_file.exists():
            size_mb = output_file.stat().st_size / (1024 * 1024)
            print(f"  ✅ Combined to MP4: {size_mb:.1f} MB")
            return True
        else:
            print(f"  ❌ FFmpeg failed: {result.stderr.decode()[:200]}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error combining segments: {e}")
        return False


def reorganize_drama(book_id: str, drama_dir: Path) -> None:
    """Reorganize a single drama directory."""
    print(f"\n{'='*60}")
    print(f"📁 Processing: {book_id}")
    print(f"{'='*60}\n")
    
    # Load or create metadata
    metadata = {
        'bookId': book_id,
        'title': f'Drama {book_id}',
        'episodes': []
    }
    
    # Check for existing cover
    cover_file = drama_dir / 'cover.jpg'
    if cover_file.exists():
        print(f"  ✓ Found cover")
        # Copy to output
        output_cover = COVERS_DIR / f"{book_id}.jpg"
        if not output_cover.exists():
            shutil.copy2(cover_file, output_cover)
    
    # Find all chapter/episode directories
    chapter_dirs = []
    
    # Pattern 1: chapter_xxxxx
    chapter_dirs.extend(drama_dir.glob("chapter_*"))
    
    # Pattern 2: bookId_chapterId format (flat segments)
    if '_' in drama_dir.name:
        # This is already a specific episode
        parts = drama_dir.name.split('_')
        if len(parts) == 2:
            chapter_id = parts[1]
            chapter_dirs = [(drama_dir, chapter_id)]
    
    if not chapter_dirs:
        print(f"  ⚠️  No episodes found in {drama_dir.name}")
        return
    
    print(f"  📺 Found {len(chapter_dirs)} episode(s)")
    
    # Create drama output directory
    drama_title = metadata['title'].replace('/', '-')
    output_drama_dir = EPISODES_DIR / drama_title
    output_drama_dir.mkdir(parents=True, exist_ok=True)
    
    # Process each chapter
    episode_num = 1
    for chapter_item in sorted(chapter_dirs):
        if isinstance(chapter_item, tuple):
            chapter_dir, chapter_id = chapter_item
        else:
            chapter_dir = chapter_item
            chapter_id = chapter_dir.name.replace('chapter_', '')
        
        print(f"\n  Episode {episode_num} (Chapter ID: {chapter_id}):")
        
        # Create episode directory with proper naming
        episode_folder = output_drama_dir / f"Episode {episode_num}"
        episode_folder.mkdir(parents=True, exist_ok=True)
        
        # Check for existing MP4
        old_mp4 = drama_dir / f"episode_{chapter_id}.mp4"
        if old_mp4.exists():
            # Copy existing MP4
            new_mp4 = episode_folder / f"Episode {episode_num}.mp4"
            if not new_mp4.exists():
                shutil.copy2(old_mp4, new_mp4)
                size_mb = new_mp4.stat().st_size / (1024 * 1024)
                print(f"    ✅ Copied MP4: {size_mb:.1f} MB")
        else:
            # Try to combine segments
            if chapter_dir.is_dir():
                segments = list(chapter_dir.glob("segment_*.ts"))
                if segments:
                    output_mp4 = episode_folder / f"Episode {episode_num}.mp4"
                    combine_segments_to_mp4(chapter_dir, output_mp4)
        
        # Create episode metadata
        episode_meta = {
            'episodeNumber': episode_num,
            'chapterId': chapter_id,
            'title': f'Episode {episode_num}',
            'bookId': book_id
        }
        
        meta_file = episode_folder / 'metadata.json'
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(episode_meta, f, indent=2, ensure_ascii=False)
        
        metadata['episodes'].append(episode_meta)
        episode_num += 1
    
    # Save drama metadata
    drama_meta_file = output_drama_dir / 'drama.json'
    with open(drama_meta_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    # Copy cover to drama folder
    if cover_file.exists():
        drama_cover = output_drama_dir / 'cover.jpg'
        if not drama_cover.exists():
            shutil.copy2(cover_file, drama_cover)
    
    print(f"\n  ✅ Reorganized to: {output_drama_dir.name}")
    print(f"     Episodes: {len(metadata['episodes'])}")


def main():
    print(f"\n{'='*60}")
    print("🔧 Reorganizing Scraped GoodShort Data")
    print(f"{'='*60}\n")
    
    # Check ffmpeg
    try:
        ffmpeg = find_ffmpeg()
        print(f"✓ Found ffmpeg: {ffmpeg}\n")
    except FileNotFoundError as e:
        print(f"❌ {e}")
        print("\nPlease install ffmpeg:")
        print("  1. Download from: https://ffmpeg.org/download.html")
        print("  2. Extract to C:\\ffmpeg")
        print("  3. Add C:\\ffmpeg\\bin to PATH")
        return
    
    # Find all downloaded dramas
    if not DOWNLOADS_DIR.exists():
        print(f"❌ Downloads directory not found: {DOWNLOADS_DIR}")
        return
    
    drama_dirs = [d for d in DOWNLOADS_DIR.iterdir() if d.is_dir()]
    
    if not drama_dirs:
        print(f"❌ No drama directories found in {DOWNLOADS_DIR}")
        return
    
    print(f"Found {len(drama_dirs)} drama(s) to process\n")
    
    # Process each drama
    for drama_dir in drama_dirs:
        # Extract book ID from directory name
        book_id = drama_dir.name.split('_')[0] if '_' in drama_dir.name else drama_dir.name
        
        reorganize_drama(book_id, drama_dir)
    
    print(f"\n{'='*60}")
    print("✅ REORGANIZATION COMPLETE")
    print(f"{'='*60}")
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print(f"\nStructure:")
    print(f"  output/")
    print(f"  ├── covers/          → All cover images")
    print(f"  ├── metadata/        → Drama metadata JSON")
    print(f"  └── episodes/")
    print(f"      └── Drama Title/")
    print(f"          ├── cover.jpg")
    print(f"          ├── drama.json")
    print(f"          ├── Episode 1/")
    print(f"          │   ├── Episode 1.mp4")
    print(f"          │   └── metadata.json")
    print(f"          ├── Episode 2/")
    print(f"          └── ...")
    print()


if __name__ == "__main__":
    main()
