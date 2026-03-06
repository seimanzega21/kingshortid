"""
Download all TS segments from M3U8 playlists
"""

import json
import requests
from pathlib import Path
from urllib.parse import urljoin
import time

def download_m3u8_segments(m3u8_file: Path, output_dir: Path):
    """Download all segments from an m3u8 playlist"""
    
    # Read m3u8 content
    with open(m3u8_file, 'r') as f:
        content = f.read()
    
    # Get base URL from HAR to construct full URLs
    # For GoodShort, segments are at: https://v2-akm.goodreels.com/mts/books/{path}/{segment}.ts
    
    # Extract segment filenames
    segments = []
    for line in content.split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            segments.append(line)
    
    if not segments:
        return 0
    
    # Construct base URL from m3u8 URL
    # We need to get the original URL from metadata
    metadata_file = m3u8_file.parent.parent / 'metadata.json'
    
    # Get episode index from folder name
    ep_folder = m3u8_file.parent.name
    ep_index = int(ep_folder.split('_')[1])
    
    # Load metadata to get original URL
    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    # Find episode with matching index
    episode = None
    for ep in metadata['episodes']:
        if ep.get('index') == ep_index:
            episode = ep
            break
    
    if not episode or 'video_url' not in episode:
        print(f"    ⚠️  No video URL for episode {ep_index}")
        return 0
    
    base_url = episode['video_url'].rsplit('/', 1)[0] + '/'
    
    # Download each segment
    downloaded = 0
    session = requests.Session()
    
    for i, segment in enumerate(segments):
        segment_file = output_dir / segment
        
        if segment_file.exists():
            continue
        
        segment_url = urljoin(base_url, segment)
        
        try:
            resp = session.get(segment_url, timeout=30)
            resp.raise_for_status()
            
            with open(segment_file, 'wb') as f:
                f.write(resp.content)
            
            downloaded += 1
            
            # Progress
            percent = ((i + 1) / len(segments)) * 100
            size_mb = len(resp.content) / 1024 / 1024
            print(f"\r      {percent:.0f}% - {i+1}/{len(segments)} segments ({size_mb:.2f} MB)", end='')
            
            # Rate limit
            time.sleep(0.1)
            
        except Exception as e:
            print(f"\n      ❌ Error downloading {segment}: {e}")
            continue
    
    print()  # New line after progress
    return downloaded


def main():
    r2_ready = Path("r2_ready")
    
    # Find all m3u8 files
    m3u8_files = list(r2_ready.rglob("*.m3u8"))
    
    print(f"📥 Found {len(m3u8_files)} m3u8 playlists to process")
    print()
    
    total_downloaded = 0
    
    for m3u8_file in m3u8_files:
        # Get drama and episode info
        drama_id = m3u8_file.parent.parent.name
        episode_folder = m3u8_file.parent.name
        
        print(f"📹 {drama_id} / {episode_folder}")
        
        # Check if segments already downloaded
        ts_files = list(m3u8_file.parent.glob("*.ts"))
        if ts_files:
            print(f"    ✅ Already has {len(ts_files)} segments")
            continue
        
        # Download segments
        print(f"    ⬇️  Downloading segments...")
        downloaded = download_m3u8_segments(m3u8_file, m3u8_file.parent)
        
        if downloaded > 0:
            total_downloaded += downloaded
            print(f"    ✅ Downloaded {downloaded} segments")
        else:
            print(f"    ⏭️  Skipped")
        
        print()
    
    print("="*60)
    print(f"✅ COMPLETE! Downloaded {total_downloaded} total segments")
    print(f"📁 Output: {r2_ready.absolute()}")
    print("="*60)


if __name__ == "__main__":
    main()
