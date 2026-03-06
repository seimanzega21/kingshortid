#!/usr/bin/env python3
"""
GOODSHORT COMPLETE DOWNLOADER
==============================

Downloads complete video episodes from GoodShort HLS URLs and organizes
them in the same structure as shortlovers/ for R2 upload.

Structure created:
goodshort/
├── [drama_slug]/
│   ├── cover.jpg
│   ├── [drama_slug]_ep_1/
│   │   ├── cover.jpg
│   │   ├── playlist.m3u8
│   │   └── goodshort_000000.ts
│   │   └── goodshort_000001.ts
│   │   └── ...

Usage:
    python download_complete_episodes.py
"""

import json
import re
import requests
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.parse import urljoin
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
SCRIPT_DIR = Path(__file__).parent
SCRAPED_DIR = SCRIPT_DIR / "scraped_dramas"
OUTPUT_DIR = SCRIPT_DIR / "r2_complete_videos"
OUTPUT_DIR.mkdir(exist_ok=True)

# Download settings
MAX_WORKERS = 5  # Parallel downloads
CHUNK_SIZE = 8192  # 8KB chunks

class HLSDownloader:
    """Download complete HLS streams with all segments"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
            'Accept-Encoding': 'identity',
            'Connection': 'keep-alive'
        })
        
        self.total_segments = 0
        self.downloaded_segments = 0
        self.failed_segments = 0
    
    def slugify(self, text: str) -> str:
        """Convert title to URL-safe slug"""
        # Convert to lowercase
        text = text.lower()
        # Replace spaces with underscores
        text = text.replace(' ', '_')
        # Remove special characters
        text = re.sub(r'[^a-z0-9_]', '', text)
        return text
    
    def parse_m3u8(self, m3u8_url: str) -> Tuple[str, List[str]]:
        """Parse HLS playlist and get segment URLs"""
        try:
            response = self.session.get(m3u8_url, timeout=30)
            response.raise_for_status()
            
            playlist_content = response.text
            base_url = m3u8_url.rsplit('/', 1)[0] + '/'
            
            segments = []
            for line in playlist_content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    # This is a segment URL
                    segment_url = urljoin(base_url, line)
                    segments.append(segment_url)
            
            return playlist_content, segments
            
        except Exception as e:
            print(f"      ❌ Failed to parse m3u8: {e}")
            return "", []
    
    def download_segment(self, segment_url: str, output_path: Path) -> bool:
        """Download single .ts segment"""
        try:
            response = self.session.get(segment_url, timeout=60, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)
            
            return True
            
        except Exception as e:
            print(f"        ❌ Failed: {e}")
            return False
    
    def download_episode(self, hls_url: str, drama_slug: str, episode_num: int, 
                        drama_folder: Path) -> bool:
        """Download complete episode with all segments"""
        
        if not hls_url:
            print(f"    ⚠️  Episode {episode_num}: No HLS URL")
            return False
        
        # Create episode folder
        ep_folder_name = f"{drama_slug}_ep_{episode_num}"
        ep_folder = drama_folder / ep_folder_name
        ep_folder.mkdir(exist_ok=True)
        
        print(f"    📺 Episode {episode_num}:")
        print(f"       Folder: {ep_folder_name}/")
        
        # Parse HLS playlist
        print(f"       [1/3] Parsing HLS playlist...")
        playlist_content, segments = self.parse_m3u8(hls_url)
        
        if not segments:
            print(f"       ❌ No segments found")
            return False
        
        print(f"       ✅ Found {len(segments)} segments")
        self.total_segments += len(segments)
        
        # Save playlist
        playlist_path = ep_folder / "playlist.m3u8"
        
        # Modify playlist to use local segment names
        local_playlist = []
        for i, line in enumerate(playlist_content.split('\n')):
            if line.strip() and not line.startswith('#'):
                # Replace with local filename
                local_playlist.append(f"goodshort_{i:06d}.ts")
            else:
                local_playlist.append(line)
        
        with open(playlist_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(local_playlist))
        
        print(f"       [2/3] Downloading {len(segments)} segments...")
        
        # Download segments with progress
        success_count = 0
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {}
            
            for i, segment_url in enumerate(segments):
                output_path = ep_folder / f"goodshort_{i:06d}.ts"
                future = executor.submit(self.download_segment, segment_url, output_path)
                futures[future] = (i, segment_url)
            
            for future in as_completed(futures):
                i, segment_url = futures[future]
                if future.result():
                    success_count += 1
                    self.downloaded_segments += 1
                    
                    # Progress indicator
                    if (i + 1) % 10 == 0 or (i + 1) == len(segments):
                        print(f"       Progress: {i + 1}/{len(segments)} segments", end='\r')
                else:
                    self.failed_segments += 1
        
        print()  # New line after progress
        
        # Copy cover to episode folder
        print(f"       [3/3] Copying cover...")
        drama_cover = drama_folder / "cover.jpg"
        if drama_cover.exists():
            shutil.copy(drama_cover, ep_folder / "cover.jpg")
        
        print(f"       ✅ Downloaded {success_count}/{len(segments)} segments")
        
        return success_count > 0
    
    def process_drama(self, drama_folder: Path) -> Dict:
        """Process complete drama with all episodes"""
        
        # Load metadata
        metadata_file = drama_folder / "metadata.json"
        episodes_file = drama_folder / "episodes.json"
        
        if not metadata_file.exists():
            print(f"  ⚠️  No metadata.json, skipping")
            return {"status": "skipped"}
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        title = metadata.get("title", drama_folder.name)
        drama_slug = self.slugify(title)
        
        # Create drama folder in output
        output_drama_folder = OUTPUT_DIR / drama_slug
        output_drama_folder.mkdir(exist_ok=True)
        
        # Copy main cover
        cover_source = drama_folder / "cover.jpg"
        if cover_source.exists():
            shutil.copy(cover_source, output_drama_folder / "cover.jpg")
            print(f"  ✅ Cover copied")
        
        # Load episodes
        episodes = []
        if episodes_file.exists():
            with open(episodes_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    episodes = data
                elif isinstance(data, dict) and "episodes" in data:
                    episodes = data["episodes"]
        
        if not episodes:
            print(f"  ⚠️  No episodes found")
            return {"status": "no_episodes"}
        
        # Filter episodes with HLS URLs
        episodes_with_hls = [ep for ep in episodes if ep.get("hlsUrl")]
        
        if not episodes_with_hls:
            print(f"  ⚠️  No episodes have HLS URLs")
            return {"status": "no_hls"}
        
        print(f"  📺 Downloading {len(episodes_with_hls)} episodes with HLS URLs...")
        
        # Download each episode
        downloaded = 0
        for episode in episodes_with_hls:
            ep_num = episode.get("episodeNumber", 1)
            hls_url = episode.get("hlsUrl", "")
            
            if self.download_episode(hls_url, drama_slug, ep_num, output_drama_folder):
                downloaded += 1
        
        return {
            "status": "success",
            "slug": drama_slug,
            "episodes_downloaded": downloaded,
            "total_episodes": len(episodes_with_hls)
        }
    
    def download_all(self):
        """Download all available dramas"""
        
        if not SCRAPED_DIR.exists():
            print(f"❌ No scraped_dramas folder found!")
            return
        
        drama_folders = [f for f in SCRAPED_DIR.iterdir() if f.is_dir()]
        
        if not drama_folders:
            print(f"❌ No drama folders found")
            return
        
        print(f"✅ Found {len(drama_folders)} dramas\n")
        
        results = []
        
        for i, folder in enumerate(drama_folders, 1):
            print(f"{'='*70}")
            print(f"📚 Drama {i}/{len(drama_folders)}: {folder.name}")
            print(f"{'='*70}")
            
            result = self.process_drama(folder)
            results.append(result)
            
            print()
        
        # Summary
        print(f"\n{'='*70}")
        print(f"✅ DOWNLOAD COMPLETE!")
        print(f"{'='*70}")
        
        successful = [r for r in results if r.get("status") == "success"]
        
        print(f"\n📊 Statistics:")
        print(f"  - Dramas processed: {len(drama_folders)}")
        print(f"  - Dramas downloaded: {len(successful)}")
        print(f"  - Total segments: {self.total_segments}")
        print(f"  - Downloaded: {self.downloaded_segments}")
        print(f"  - Failed: {self.failed_segments}")
        
        if successful:
            print(f"\n✅ Successfully downloaded dramas:")
            for result in successful:
                print(f"  - {result['slug']}: {result['episodes_downloaded']}/{result['total_episodes']} episodes")
        
        print(f"\n📁 Output: {OUTPUT_DIR}")
        print(f"🚀 Next: Upload to R2 with upload_complete_to_r2.py")
        print()

def main():
    print("\n" + "="*70)
    print("🎬 GOODSHORT COMPLETE DOWNLOADER")
    print("="*70 + "\n")
    
    downloader = HLSDownloader()
    downloader.download_all()

if __name__ == "__main__":
    main()
