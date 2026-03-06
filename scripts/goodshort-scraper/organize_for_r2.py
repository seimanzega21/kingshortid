#!/usr/bin/env python3
"""
ORGANIZE CAPTURED SEGMENTS FOR R2 UPLOAD
=========================================

Organizes downloaded segments into R2-ready structure:

captured_complete/episode_X/ → r2_ready/drama_slug/drama_slug_ep_N/
"""

import json
import shutil
from pathlib import Path
import re

# Paths
SCRIPT_DIR = Path(__file__).parent
CAPTURED_DIR = SCRIPT_DIR / "captured_complete"
OUTPUT_DIR = SCRIPT_DIR / "r2_ready/goodshort"
SCRAPED_DIR = SCRIPT_DIR / "scraped_dramas"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def slugify(text: str) -> str:
    """Convert to URL-safe slug"""
    text = text.lower()
    text = text.replace(' ', '_')
    text = re.sub(r'[^a-z0-9_]', '', text)
    return text

def find_episode_metadata(episode_id: str):
    """Find metadata for episode ID"""
    
    # Search all scraped dramas
    for drama_folder in SCRAPED_DIR.iterdir():
        if not drama_folder.is_dir():
            continue
        
        episodes_file = drama_folder / "episodes.json"
        if not episodes_file.exists():
            continue
        
        with open(episodes_file, 'r', encoding='utf-8') as f:
            episodes = json.load(f)
        
        for ep in episodes:
            if str(ep.get('id')) == episode_id or str(ep.get('episode_id')) == episode_id:
                # Found it!
                metadata_file = drama_folder / "metadata.json"
                with open(metadata_file, 'r') as f:
                    drama_meta = json.load(f)
                
                return {
                    'drama_title': drama_meta.get('title'),
                    'episode_number': ep.get('episodeNumber', ep.get('episode')),
                    'drama_folder': drama_folder
                }
    
    return None

def create_playlist(segment_folder: Path, output_file: Path):
    """Create HLS playlist for segments"""
    
    segments = sorted(segment_folder.glob("segment_*.ts"))
    
    with open(output_file, 'w') as f:
        f.write("#EXTM3U\n")
        f.write("#EXT-X-VERSION:3\n")
        f.write("#EXT-X-TARGETDURATION:10\n")
        f.write("#EXT-X-MEDIA-SEQUENCE:0\n")
        
        for seg in segments:
            f.write("#EXTINF:10.0,\n")
            f.write(f"{seg.name}\n")
        
        f.write("#EXT-X-ENDLIST\n")

def organize_for_r2():
    """Organize all captured episodes"""
    
    print("\n" + "="*70)
    print("ORGANIZE FOR R2 UPLOAD")
    print("="*70)
    print()
    
    episode_folders = list(CAPTURED_DIR.glob("episode_*"))
    
    print(f"Found {len(episode_folders)} captured episodes")
    print()
    
    organized = 0
    skipped = 0
    
    for ep_folder in episode_folders:
        episode_id = ep_folder.name.replace("episode_", "")
        
        print(f"Episode {episode_id}:")
        
        # Find metadata
        meta = find_episode_metadata(episode_id)
        
        if not meta:
            print(f"  ⚠️  Metadata not found - keeping as episode_{episode_id}")
            # Copy as-is
            dest = OUTPUT_DIR / f"unknown_drama/episode_{episode_id}"
            dest.mkdir(parents=True, exist_ok=True)
            
            # Copy segments
            for seg in ep_folder.glob("*.ts"):
                shutil.copy(seg, dest / seg.name)
            
            # Create playlist
            create_playlist(dest, dest / "playlist.m3u8")
            
            skipped += 1
            continue
        
        # Create organized structure
        drama_slug = slugify(meta['drama_title'])
        ep_num = meta['episode_number']
        
        folder_name = f"{drama_slug}_ep_{ep_num}"
        dest_folder = OUTPUT_DIR / drama_slug / folder_name
        dest_folder.mkdir(parents=True, exist_ok=True)
        
        print(f"  → {drama_slug}/{folder_name}/")
        
        # Copy segments
        segment_count = 0
        for seg in ep_folder.glob("segment_*.ts"):
            shutil.copy(seg, dest_folder / seg.name)
            segment_count += 1
        
        # Copy cover if exists
        cover_src = meta['drama_folder'] / "cover.jpg"
        if cover_src.exists():
            shutil.copy(cover_src, dest_folder / "cover.jpg")
        
        # Create playlist
        create_playlist(dest_folder, dest_folder / "playlist.m3u8")
        
        print(f"  ✅ {segment_count} segments + playlist")
        organized += 1
    
    print()
    print("="*70)
    print("ORGANIZATION COMPLETE!")
    print("="*70)
    print(f"Organized: {organized}")
    print(f"Skipped: {skipped}")
    print(f"Output: {OUTPUT_DIR}/")
    print()
    print("Ready for: python upload_to_r2.py")
    print()

if __name__ == "__main__":
    organize_for_r2()
