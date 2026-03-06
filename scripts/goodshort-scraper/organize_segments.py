#!/usr/bin/env python3
"""
SEGMENT ORGANIZER & R2 UPLOADER
================================

Organizes captured video segments into proper structure and uploads to R2.

Input: captured_segments/
  - episode_{id}_playlist.m3u8
  - episode_{id}_segment_000000.ts
  - episode_{id}_segment_000001.ts

Output: r2_complete_videos/
  - {drama_slug}/
    - cover.jpg
    - {drama_slug}_ep_1/
      - cover.jpg
      - playlist.m3u8
      - goodshort_000000.ts
      - goodshort_000001.ts
"""

import json
import shutil
from pathlib import Path
from collections import defaultdict
from dotenv import load_dotenv
import boto3
import os

# Load env
load_dotenv()

# Paths
SCRIPT_DIR = Path(__file__).parent
CAPTURED_DIR = SCRIPT_DIR / "captured_segments"
SCRAPED_DIR = SCRIPT_DIR / "scraped_dramas"
OUTPUT_DIR = SCRIPT_DIR / "r2_complete_videos"
OUTPUT_DIR.mkdir(exist_ok=True)

# R2 Config
R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET = os.getenv("R2_BUCKET", "kingshort")
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL")

class SegmentOrganizer:
    """Organize segments and upload to R2"""
    
    def __init__(self):
        self.episodes_data = defaultdict(lambda: {
            'playlist': None,
            'segments': []
        })
        
        # R2 client
        if R2_ACCOUNT_ID and R2_ACCESS_KEY_ID:
            self.s3 = boto3.client(
                's3',
                endpoint_url=f'https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
                aws_access_key_id=R2_ACCESS_KEY_ID,
                aws_secret_access_key=R2_SECRET_ACCESS_KEY,
                region_name='auto'
            )
            self.can_upload = True
        else:
            self.can_upload = False
    
    def slugify(self, text: str) -> str:
        """Convert to slug"""
        import re
        text = text.lower().replace(' ', '_')
        return re.sub(r'[^a-z0-9_]', '', text)
    
    def find_episode_metadata(self, episode_id: str):
        """Find metadata for episode from scraped_dramas"""
        for drama_folder in SCRAPED_DIR.iterdir():
            if not drama_folder.is_dir():
                continue
            
            episodes_file = drama_folder / "episodes.json"
            if episodes_file.exists():
                with open(episodes_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    episodes = data if isinstance(data, list) else data.get("episodes", [])
                    
                    for ep in episodes:
                        if str(ep.get("episodeId")) == episode_id:
                            # Found it! Load drama metadata too
                            metadata_file = drama_folder / "metadata.json"
                            metadata = {}
                            if metadata_file.exists():
                                with open(metadata_file, 'r', encoding='utf-8') as mf:
                                    metadata = json.load(mf)
                            
                            return {
                                'drama_folder': drama_folder,
                                'drama_metadata': metadata,
                                'episode': ep
                            }
        return None
    
    def organize_segments(self):
        """Organize captured segments into proper structure"""
        if not CAPTURED_DIR.exists():
            print("❌ No captured_segments folder found!")
            return
        
        # Group files by episode
        for file_path in CAPTURED_DIR.glob("episode_*"):
            parts = file_path.stem.split('_')
            if len(parts) < 3:
                continue
            
            episode_id = parts[1]
            file_type = parts[2]
            
            if file_type == "playlist":
                self.episodes_data[episode_id]['playlist'] = file_path
            elif file_type == "segment":
                self.episodes_data[episode_id]['segments'].append(file_path)
        
        print(f"📊 Found {len(self.episodes_data)} episodes with segments\n")
        
        # Process each episode
        for episode_id, data in self.episodes_data.items():
            print(f"{'='*70}")
            print(f"📺 Episode ID: {episode_id}")
            print(f"{'='*70}")
            
            # Find metadata
            meta = self.find_episode_metadata(episode_id)
            if not meta:
                print(f"  ⚠️  No metadata found, skipping")
                continue
            
            drama_meta = meta['drama_metadata']
            episode_meta = meta['episode']
            drama_folder = meta['drama_folder']
            
            drama_title = drama_meta.get('title', 'Unknown')
            drama_slug = self.slugify(drama_title)
            episode_num = episode_meta.get('episodeNumber', 1)
            
            print(f"  Drama: {drama_title}")
            print(f"  Episode: {episode_num}")
            print(f"  Segments: {len(data['segments'])}")
            
            # Create output structure
            output_drama = OUTPUT_DIR / drama_slug
            output_drama.mkdir(exist_ok=True)
            
            # Copy main cover
            cover_src = drama_folder / "cover.jpg"
            if cover_src.exists():
                shutil.copy(cover_src, output_drama / "cover.jpg")
            
            # Create episode folder
            ep_folder_name = f"{drama_slug}_ep_{episode_num}"
            ep_folder = output_drama / ep_folder_name
            ep_folder.mkdir(exist_ok=True)
            
            # Copy playlist
            if data['playlist']:
                shutil.copy(data['playlist'], ep_folder / "playlist.m3u8")
            
            # Copy and rename segments
            data['segments'].sort()
            for i, segment_file in enumerate(data['segments']):
                new_name = f"goodshort_{i:06d}.ts"
                shutil.copy(segment_file, ep_folder / new_name)
            
            # Copy episode cover
            shutil.copy(cover_src, ep_folder / "cover.jpg")
            
            print(f"  ✅ Organized: {ep_folder_name}/")
            
            # Upload to R2
            if self.can_upload:
                self.upload_episode_to_r2(drama_slug, ep_folder_name, ep_folder)
            
            print()
        
        print(f"\n✅ Organization complete!")
        print(f"📁 Output: {OUTPUT_DIR}")
        
        if self.can_upload:
            print(f"\n🌐 Videos available at:")
            print(f"   {R2_PUBLIC_URL}/goodshort/{{drama_slug}}/{{episode_folder}}/")
    
    def upload_episode_to_r2(self, drama_slug: str, ep_folder_name: str, ep_folder: Path):
        """Upload episode to R2"""
        print(f"  ☁️  Uploading to R2...")
        
        uploaded = 0
        for file_path in ep_folder.iterdir():
            if not file_path.is_file():
                continue
            
            # content type
            content_type = 'application/octet-stream'
            if file_path.suffix == '.m3u8':
                content_type = 'application/vnd.apple.mpegurl'
            elif file_path.suffix == '.ts':
                content_type = 'video/mp2t'
            elif file_path.suffix == '.jpg':
                content_type = 'image/jpeg'
            
            # S3 key
            s3_key = f"goodshort/{drama_slug}/{ep_folder_name}/{file_path.name}"
            
            try:
                self.s3.upload_file(
                    str(file_path),
                    R2_BUCKET,
                    s3_key,
                    ExtraArgs={'ContentType': content_type}
                )
                uploaded += 1
            except Exception as e:
                print(f"      ❌ Upload failed: {file_path.name}: {e}")
        
        print(f"      ✅ Uploaded {uploaded} files")

def main():
    print("\n" + "="*70)
    print("📦 SEGMENT ORGANIZER & R2 UPLOADER")
    print("="*70 + "\n")
    
    organizer = SegmentOrganizer()
    organizer.organize_segments()

if __name__ == "__main__":
    main()
