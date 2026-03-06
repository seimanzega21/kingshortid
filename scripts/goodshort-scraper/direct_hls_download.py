#!/usr/bin/env python3
"""
DIRECT HLS DOWNLOADER - Level 3 (Dewa Mode)
===========================================

Downloads video segments directly from GoodShort CDN using known HLS URLs.
No emulator, no Frida - pure Python requests!

Strategy:
1. Use captured HLS URLs from metadata
2. Parse m3u8 playlist
3. Download all .ts segments
4. Organize in shortlovers-style structure
5. Upload to R2
"""

import requests
import m3u8
import re
from pathlib import Path
from urllib.parse import urljoin
import json
from typing import List, Dict, Tuple

# Config
SCRIPT_DIR = Path(__file__).parent
SCRAPED_DIR = SCRIPT_DIR / "scraped_dramas"
OUTPUT_DIR = SCRIPT_DIR / "r2_complete_videos"
OUTPUT_DIR.mkdir(exist_ok=True)

# Headers to mimic GoodShort app
HEADERS = {
    'User-Agent': 'GoodShort/2.5.1 (Linux; Android 11; Vivo S1 Pro)',
    'Accept': '*/*',
    'Accept-Encoding': 'identity',
    'Connection': 'keep-alive'
}

class DirectHLSDownloader:
    """Direct download from GoodShort CDN"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        
        self.stats = {
            'episodes_processed': 0,
            'segments_downloaded': 0,
            'bytes_downloaded': 0,
            'errors': []
        }
    
    def test_url_access(self, hls_url: str) -> bool:
        """Test if URL is accessible"""
        print(f"\n🔍 Testing URL access:")
        print(f"   {hls_url[:80]}...")
        
        try:
            response = self.session.get(hls_url, timeout=10)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ SUCCESS! URL is accessible")
                print(f"   Content length: {len(response.text)} bytes")
                print(f"   First 200 chars: {response.text[:200]}")
                return True
            else:
                print(f"   ❌ Failed: HTTP {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def parse_m3u8(self, hls_url: str) -> Tuple[str, List[str]]:
        """
        Parse HLS playlist and get segment URLs.
        Returns: (playlist_content, segment_urls)
        """
        try:
            response = self.session.get(hls_url, timeout=30)
            response.raise_for_status()
            
            playlist = m3u8.loads(response.text)
            base_url = hls_url.rsplit('/', 1)[0] + '/'
            
            segments = []
            for segment in playlist.segments:
                segment_url = urljoin(base_url, segment.uri)
                segments.append(segment_url)
            
            print(f"   ✅ Parsed playlist: {len(segments)} segments")
            return response.text, segments
            
        except Exception as e:
            print(f"   ❌ Parse failed: {e}")
            return "", []
    
    def download_segment(self, segment_url: str, output_path: Path) -> bool:
        """Download single .ts segment"""
        try:
            response = self.session.get(segment_url, timeout=60, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            size = output_path.stat().st_size
            self.stats['bytes_downloaded'] += size
            self.stats['segments_downloaded'] += 1
            
            return True
            
        except Exception as e:
            self.stats['errors'].append(str(e))
            return False
    
    def download_episode(self, hls_url: str, drama_slug: str, 
                        episode_num: int, output_dir: Path) -> bool:
        """Download complete episode"""
        
        if not hls_url:
            print(f"  ⚠️  Episode {episode_num}: No HLS URL")
            return False
        
        # Create episode folder
        ep_folder = output_dir / f"{drama_slug}_ep_{episode_num}"
        ep_folder.mkdir(exist_ok=True)
        
        print(f"\n  📺 Episode {episode_num}:")
        print(f"     Folder: {ep_folder.name}/")
        
        # Test URL first
        if not self.test_url_access(hls_url):
            print(f"     ❌ URL not accessible, skipping")
            return False
        
        # Parse playlist
        print(f"     [1/3] Parsing HLS playlist...")
        playlist_content, segments = self.parse_m3u8(hls_url)
        
        if not segments:
            print(f"     ❌ No segments found")
            return False
        
        # Save playlist locally
        playlist_path = ep_folder / "playlist.m3u8"
        
        # Modify playlist for local playback
        local_playlist_lines = []
        for i, line in enumerate(playlist_content.split('\n')):
            if line.strip() and not line.startswith('#'):
                # Replace with local filename
                local_playlist_lines.append(f"goodshort_{i:06d}.ts")
            else:
                local_playlist_lines.append(line)
        
        with open(playlist_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(local_playlist_lines))
        
        # Download segments
        print(f"     [2/3] Downloading {len(segments)} segments...")
        
        success = 0
        for i, segment_url in enumerate(segments):
            output_path = ep_folder / f"goodshort_{i:06d}.ts"
            
            if self.download_segment(segment_url, output_path):
                success += 1
                if (i + 1) % 10 == 0:
                    print(f"        Progress: {i + 1}/{len(segments)}")
            else:
                print(f"        ❌ Failed: segment {i}")
        
        print(f"     [3/3] Downloaded {success}/{len(segments)} segments")
        self.stats['episodes_processed'] += 1
        
        return success > 0
    
    def slugify(self, text: str) -> str:
        """Convert to URL-safe slug"""
        text = text.lower().replace(' ', '_')
        return re.sub(r'[^a-z0-9_]', '', text)
    
    def process_all(self):
        """Process all scraped dramas"""
        
        if not SCRAPED_DIR.exists():
            print("❌ No scraped_dramas folder!")
            return
        
        dramas = [d for d in SCRAPED_DIR.iterdir() if d.is_dir()]
        print(f"\n✅ Found {len(dramas)} dramas\n")
        
        for drama_folder in dramas:
            metadata_file = drama_folder / "metadata.json"
            episodes_file = drama_folder / "episodes.json"
            
            if not metadata_file.exists() or not episodes_file.exists():
                continue
            
            # Load data
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            with open(episodes_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                episodes = data if isinstance(data, list) else data.get('episodes', [])
            
            # Filter episodes with HLS
            episodes_with_hls = [ep for ep in episodes if ep.get('hlsUrl')]
            
            if not episodes_with_hls:
                continue
            
            print(f"{'='*70}")
            print(f"📚 {metadata.get('title', 'Unknown')}")
            print(f"{'='*70}")
            print(f"Episodes with HLS: {len(episodes_with_hls)}")
            
            drama_slug = self.slugify(metadata.get('title', 'unknown'))
            output_drama = OUTPUT_DIR / drama_slug
            output_drama.mkdir(exist_ok=True)
            
            # Copy cover
            cover_src = drama_folder / "cover.jpg"
            if cover_src.exists():
                import shutil
                shutil.copy(cover_src, output_drama / "cover.jpg")
            
            # Download episodes
            for episode in episodes_with_hls:
                ep_num = episode.get('episodeNumber', 1)
                hls_url = episode.get('hlsUrl', '')
                
                self.download_episode(hls_url, drama_slug, ep_num, output_drama)
        
        # Final stats
        print(f"\n{'='*70}")
        print(f"✅ DOWNLOAD COMPLETE!")
        print(f"{'='*70}")
        print(f"\n📊 Statistics:")
        print(f"  Episodes: {self.stats['episodes_processed']}")
        print(f"  Segments: {self.stats['segments_downloaded']}")
        print(f"  Data: {self.stats['bytes_downloaded'] / 1024 / 1024:.2f} MB")
        print(f"  Errors: {len(self.stats['errors'])}")
        print(f"\n📁 Output: {OUTPUT_DIR}")
        print()

def main():
    print("\n" + "="*70)
    print("🎯 DIRECT HLS DOWNLOADER - Level 3 (Dewa Mode)")
    print("="*70 + "\n")
    
    downloader = DirectHLSDownloader()
    downloader.process_all()

if __name__ == "__main__":
    main()
