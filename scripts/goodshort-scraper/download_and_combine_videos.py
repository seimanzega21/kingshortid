"""
Download and Combine Video Segments - Phase 4 Step 2
Downloads all .ts segments and combines them into MP4 files per episode
"""

import json
import requests
from pathlib import Path
import time
import subprocess
import re
from collections import defaultdict

# Load data
with open('extracted_data_complete/video_segments.json', 'r', encoding='utf-8') as f:
    video_segments = json.load(f)

with open('extracted_data_complete/dramas.json', 'r', encoding='utf-8') as f:
    dramas = json.load(f)

with open('extracted_data_complete/complete_episodes.json', 'r', encoding='utf-8') as f:
    complete_episodes = json.load(f)

# Create output directories
segments_dir = Path("downloaded_media/segments")
videos_dir = Path("downloaded_media/videos")
segments_dir.mkdir(parents=True, exist_ok=True)
videos_dir.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("DOWNLOADING VIDEO SEGMENTS")
print("=" * 70)

# Download headers
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': '*/*',
    'Accept-Encoding': 'identity',  # Critical for GoodShort CDN
    'Referer': 'https://www.goodreels.com/',
    'Origin': 'https://www.goodreels.com'
}

total_segments = sum(len(segs) for segs in video_segments.values())
downloaded_count = 0
failed_segments = []

for video_key, segments in video_segments.items():
    book_id, episode_id = video_key.split('_')
    drama = dramas.get(episode_id, {})
    drama_title = drama.get('title', 'Unknown')
    
    print(f"\n{'=' * 70}")
    print(f"Drama: {drama_title}")
    print(f"Segments: {len(segments)}")
    print(f"{'=' * 70}")
    
    # Group segments by episode part (folder hash)
    parts = defaultdict(list)
    for url in segments:
        match = re.search(r'/(\w+)/720p/(\w+)_720p_(\d+)\.ts', url)
        if match:
            folder_hash = match.group(1)
            segment_num = int(match.group(3))
            parts[folder_hash].append({
                'url': url,
                'segment_num': segment_num
            })
    
    # Download each part (episode)
    for part_idx, (folder_hash, part_segments) in enumerate(sorted(parts.items()), 1):
        # Sort by segment number
        part_segments.sort(key=lambda x: x['segment_num'])
        
        print(f"\n  Part {part_idx}/{len(parts)} ({folder_hash[:8]}...)")
        print(f"    Segments: {len(part_segments)}")
        
        # Create subfolder for this part
        part_dir = segments_dir / f"{episode_id}_part{part_idx:02d}"
        part_dir.mkdir(exist_ok=True)
        
        # Download segments
        segment_files = []
        for seg in part_segments:
            url = seg['url']
            seg_num = seg['segment_num']
            filename = f"segment_{seg_num:03d}.ts"
            filepath = part_dir / filename
            
            # Skip if already downloaded
            if filepath.exists():
                segment_files.append(filepath)
                continue
            
            try:
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                segment_files.append(filepath)
                downloaded_count += 1
                
                # Progress update every 10 segments
                if downloaded_count % 10 == 0:
                    progress = (downloaded_count / total_segments) * 100
                    print(f"    Progress: {downloaded_count}/{total_segments} ({progress:.1f}%)")
                
                # Small delay
                time.sleep(0.1)
                
            except Exception as e:
                print(f"    ❌ Failed segment {seg_num}: {e}")
                failed_segments.append({
                    'url': url,
                    'error': str(e)
                })
        
        print(f"    ✅ Downloaded {len(segment_files)} segments")
        
        # Combine segments to MP4 using ffmpeg
        print(f"    🔧 Combining to MP4...")
        
        safe_title = drama_title.replace(' ', '_').replace(',', '').replace(':', '')
        output_filename = f"{episode_id}_{safe_title}_ep{part_idx:02d}.mp4"
        output_path = videos_dir / output_filename
        
        # Create concat file
        concat_file = part_dir / "concat_list.txt"
        with open(concat_file, 'w') as f:
            for seg_file in segment_files:
                # Use relative path
                f.write(f"file '{seg_file.absolute()}'\n")
        
        # Run ffmpeg
        try:
            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(concat_file),
                '-c', 'copy',  # Copy without re-encoding (faster)
                '-y',  # Overwrite
                str(output_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 min timeout
            )
            
            if result.returncode == 0 and output_path.exists():
                file_size = output_path.stat().st_size / (1024 * 1024)  # MB
                print(f"    ✅ Created: {output_filename} ({file_size:.1f} MB)")
            else:
                print(f"    ❌ FFmpeg failed: {result.stderr[:200]}")
        
        except FileNotFoundError:
            print(f"    ⚠️ FFmpeg not found - segments downloaded but not combined")
            print(f"       Install FFmpeg to combine: https://ffmpeg.org/download.html")
        except Exception as e:
            print(f"    ❌ Combine error: {e}")

print("\n" + "=" * 70)
print("DOWNLOAD SUMMARY")
print("=" * 70)
print(f"\nTotal Segments: {total_segments}")
print(f"Downloaded: {downloaded_count}")
print(f"Failed: {len(failed_segments)}")

# List combined videos
video_files = list(videos_dir.glob("*.mp4"))
print(f"\nCombined Videos: {len(video_files)}")
for vf in sorted(video_files):
    size_mb = vf.stat().st_size / (1024 * 1024)
    print(f"  - {vf.name} ({size_mb:.1f} MB)")

print(f"\n📁 Segments saved to: {segments_dir}/")
print(f"📁 Videos saved to: {videos_dir}/")

# Save failed segments log
if failed_segments:
    failed_log = Path("downloaded_media/failed_segments.json")
    with open(failed_log, 'w') as f:
        json.dump(failed_segments, f, indent=2)
    print(f"\n⚠️ Failed segments logged: {failed_log}")

print("\n✅ Download complete!")
