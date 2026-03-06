#!/usr/bin/env python3
"""
COMPLETE DRAMA CAPTURE - ALL IN ONE
====================================

Captures COMPLETE drama with:
- ✅ Metadata (title, description, genre, etc)
- ✅ Cover image
- ✅ Episode list with HLS URLs
- ✅ ALL video segments for ALL episodes
- ✅ Organized for R2 upload

ONE COMMAND = COMPLETE DRAMA!
"""

import subprocess
import json
import time
from pathlib import Path
import sys

# Paths
SCRIPT_DIR = Path(__file__).parent
SCRAPED_DIR = SCRIPT_DIR / "scraped_dramas"
OUTPUT_DIR = SCRIPT_DIR / "complete_dramas"
OUTPUT_DIR.mkdir(exist_ok=True)

class CompleteDramaCaptureSystem:
    """Capture complete drama with all assets"""
    
    def __init__(self, drama_slug: str):
        self.drama_slug = drama_slug
        self.drama_folder = SCRAPED_DIR / drama_slug
        self.output_folder = OUTPUT_DIR / drama_slug
        self.output_folder.mkdir(exist_ok=True)
        
        # Load metadata
        self.metadata = self._load_metadata()
        self.episodes = self._load_episodes()
    
    def _load_metadata(self):
        """Load drama metadata"""
        metadata_file = self.drama_folder / "metadata.json"
        if not metadata_file.exists():
            raise FileNotFoundError(f"Metadata not found: {metadata_file}")
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_episodes(self):
        """Load episode list"""
        episodes_file = self.drama_folder / "episodes.json"
        if not episodes_file.exists():
            raise FileNotFoundError(f"Episodes not found: {episodes_file}")
        
        with open(episodes_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def print_status(self):
        """Print drama status"""
        print("\n" + "="*70)
        print(f"COMPLETE DRAMA CAPTURE: {self.metadata.get('title')}")
        print("="*70)
        print()
        print(f"Drama: {self.metadata.get('title')}")
        print(f"Total Episodes: {len(self.episodes)}")
        print(f"Genre: {self.metadata.get('genre', 'Unknown')}")
        print()
        
        # Check assets
        has_cover = (self.drama_folder / "cover.jpg").exists()
        print(f"Metadata: ✅")
        print(f"Cover: {'✅' if has_cover else '❌'}")
        print(f"Episodes: ✅ ({len(self.episodes)} episodes)")
        print()
    
    def capture_all_episodes_with_http_toolkit(self):
        """Guide user through HTTP Toolkit capture for all episodes"""
        
        print("="*70)
        print("VIDEO CAPTURE WORKFLOW")
        print("="*70)
        print()
        print("STEPS:")
        print()
        print("1. HTTP Toolkit Setup")
        print("   - Open HTTP Toolkit")
        print("   - Click 'Android Device via ADB'")
        print("   - Wait for 'Intercepting' status")
        print()
        print("2. Play ALL Episodes")
        print(f"   - Open GoodShort → {self.metadata.get('title')}")
        print(f"   - Play Episode 1-{len(self.episodes)}")
        print("   - Let each episode buffer (30-60 seconds)")
        print("   - Continue to next episode")
        print()
        print("3. Export HAR")
        print("   - After all episodes buffered")
        print("   - File → Export → HAR")
        print(f"   - Save as: {self.drama_slug}_complete.har")
        print(f"   - Location: {SCRIPT_DIR}/")
        print()
        
        input("Press ENTER after HAR export complete...")
        
        # Find HAR file
        har_file = SCRIPT_DIR / f"{self.drama_slug}_complete.har"
        if not har_file.exists():
            print()
            print(f"❌ HAR file not found: {har_file}")
            print()
            print("Please export HAR and try again")
            return False
        
        # Download segments
        print()
        print("Downloading all segments...")
        cmd = [
            sys.executable,
            str(SCRIPT_DIR / "ultimate_capture.py"),
            str(har_file)
        ]
        
        result = subprocess.run(cmd)
        
        if result.returncode != 0:
            print("❌ Download failed!")
            return False
        
        return True
    
    def organize_complete_drama(self):
        """Organize into final structure"""
        
        import shutil
        import re
        
        print()
        print("="*70)
        print("ORGANIZING COMPLETE DRAMA")
        print("="*70)
        print()
        
        # Create drama folder
        drama_output = self.output_folder
        drama_output.mkdir(exist_ok=True)
        
        # Copy cover
        cover_src = self.drama_folder / "cover.jpg"
        if cover_src.exists():
            shutil.copy(cover_src, drama_output / "cover.jpg")
            print("✅ Drama cover copied")
        
        # Copy metadata
        shutil.copy(
            self.drama_folder / "metadata.json",
            drama_output / "metadata.json"
        )
        print("✅ Metadata copied")
        
        # Copy episodes metadata
        shutil.copy(
            self.drama_folder / "episodes.json",
            drama_output / "episodes.json"
        )
        print("✅ Episode list copied")
        
        # Organize video segments
        captured_dir = SCRIPT_DIR / "captured_complete"
        
        if not captured_dir.exists():
            print("⚠️  No captured segments found")
            return
        
        episode_folders = list(captured_dir.glob("episode_*"))
        print(f"\nFound {len(episode_folders)} captured episodes")
        print()
        
        for ep_folder in episode_folders:
            episode_id = ep_folder.name.replace("episode_", "")
            
            # Find matching episode number
            ep_num = None
            for ep in self.episodes:
                if str(ep.get('id')) == episode_id or str(ep.get('episode_id')) == episode_id:
                    ep_num = ep.get('episodeNumber', ep.get('episode'))
                    break
            
            if not ep_num:
                print(f"  ⚠️  Episode {episode_id}: No metadata match")
                continue
            
            # Create episode folder
            ep_output = drama_output / f"{self.drama_slug}_ep_{ep_num}"
            ep_output.mkdir(exist_ok=True)
            
            # Copy segments
            segment_count = 0
            for seg in ep_folder.glob("segment_*.ts"):
                shutil.copy(seg, ep_output / seg.name)
                segment_count += 1
            
            # Copy cover
            if cover_src.exists():
                shutil.copy(cover_src, ep_output / "cover.jpg")
            
            # Create playlist
            self._create_playlist(ep_output)
            
            print(f"  ✅ Episode {ep_num}: {segment_count} segments")
        
        print()
        print("="*70)
        print("COMPLETE DRAMA READY!")
        print("="*70)
        print(f"Location: {drama_output}/")
        print()
        print("Structure:")
        print(f"  {self.drama_slug}/")
        print(f"    ├── cover.jpg")
        print(f"    ├── metadata.json")
        print(f"    ├── episodes.json")
        for i in range(1, min(4, len(self.episodes)+1)):
            print(f"    ├── {self.drama_slug}_ep_{i}/")
            print(f"    │   ├── cover.jpg")
            print(f"    │   ├── playlist.m3u8")
            print(f"    │   └── segment_*.ts")
        if len(self.episodes) > 3:
            print(f"    └── ... ({len(self.episodes)} episodes total)")
        print()
        print("Ready for R2 upload!")
        print()
    
    def _create_playlist(self, episode_folder: Path):
        """Create HLS playlist"""
        segments = sorted(episode_folder.glob("segment_*.ts"))
        
        playlist = episode_folder / "playlist.m3u8"
        with open(playlist, 'w') as f:
            f.write("#EXTM3U\n")
            f.write("#EXT-X-VERSION:3\n")
            f.write("#EXT-X-TARGETDURATION:10\n")
            f.write("#EXT-X-MEDIA-SEQUENCE:0\n")
            
            for seg in segments:
                f.write("#EXTINF:10.0,\n")
                f.write(f"{seg.name}\n")
            
            f.write("#EXT-X-ENDLIST\n")
    
    def run_complete_capture(self):
        """Execute complete capture workflow"""
        
        self.print_status()
        
        # Check if already has segments
        print("OPTIONS:")
        print()
        print("A. Capture videos with HTTP Toolkit (capture all episodes)")
        print("B. Skip video capture (organize existing metadata only)")
        print()
        
        choice = input("Choose (A/B): ").strip().upper()
        
        if choice == 'A':
            success = self.capture_all_episodes_with_http_toolkit()
            if not success:
                print("Video capture failed. Organizing metadata only...")
        
        # Organize everything
        self.organize_complete_drama()

def list_available_dramas():
    """List dramas ready for capture"""
    
    print("\n" + "="*70)
    print("AVAILABLE DRAMAS FOR COMPLETE CAPTURE")
    print("="*70)
    print()
    
    dramas = []
    for drama_folder in SCRAPED_DIR.iterdir():
        if not drama_folder.is_dir():
            continue
        
        metadata_file = drama_folder / "metadata.json"
        episodes_file = drama_folder / "episodes.json"
        cover_file = drama_folder / "cover.jpg"
        
        if not metadata_file.exists():
            continue
        
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        episodes = []
        if episodes_file.exists():
            with open(episodes_file, 'r', encoding='utf-8') as f:
                episodes = json.load(f)
        
        status = "✅ READY" if (episodes_file.exists() and cover_file.exists()) else "⚠️  INCOMPLETE"
        
        dramas.append({
            'slug': drama_folder.name,
            'title': metadata.get('title'),
            'episodes': len(episodes),
            'status': status
        })
    
    for i, drama in enumerate(dramas, 1):
        print(f"{i}. {drama['title']}")
        print(f"   Slug: {drama['slug']}")
        print(f"   Episodes: {drama['episodes']}")
        print(f"   Status: {drama['status']}")
        print()
    
    return dramas

def main():
    """Main entry point"""
    
    if len(sys.argv) > 1:
        drama_slug = sys.argv[1]
    else:
        dramas = list_available_dramas()
        
        if not dramas:
            print("❌ No dramas found!")
            print()
            print("Run metadata scraping first:")
            print("  .\\auto-scrape-production.bat")
            return
        
        print("Enter drama number or slug:")
        choice = input("> ").strip()
        
        try:
            idx = int(choice) - 1
            drama_slug = dramas[idx]['slug']
        except:
            drama_slug = choice
    
    # Run capture
    try:
        capturer = CompleteDramaCaptureSystem(drama_slug)
        capturer.run_complete_capture()
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print()
        print("Make sure drama has been scraped first!")

if __name__ == "__main__":
    main()
