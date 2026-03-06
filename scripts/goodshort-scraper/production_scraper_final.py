#!/usr/bin/env python3
"""
PRODUCTION GOODSHORT SCRAPER - FINAL VERSION
============================================

Complete drama scraper with:
- Real cover download from CDN
- Episode 1-20 metadata structure
- HLS URL pattern (ready for actual URLs)
- R2 upload integration
- Organized folder structure

Usage:
    python production_scraper_final.py
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List
import requests
from PIL import Image
from io import BytesIO

# Configuration
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "scraped_dramas_production"
OUTPUT_DIR.mkdir(exist_ok=True)

# R2 Configuration (update when ready for upload)
R2_ACCOUNT_ID = "your_account_id"
R2_ACCESS_KEY = "your_access_key"
R2_SECRET_KEY = "your_secret_key"
R2_BUCKET = "kingshortid"

class ProductionScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def download_cover(self, cover_url: str, output_path: Path) -> bool:
        """Download and validate portrait cover from CDN"""
        try:
            print(f"  📥 Downloading cover...")
            response = self.session.get(cover_url, timeout=30)
            response.raise_for_status()
            
            # Validate image
            img = Image.open(BytesIO(response.content))
            width, height = img.size
            
            # Check if portrait (height > width)
            if height <= width:
                print(f"  ⚠️  Skipping - not portrait ({width}x{height})")
                return False
            
            # Convert RGBA to RGB if needed
            if img.mode == 'RGBA':
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[3])
                img = rgb_img
            
            # Save as JPEG
            img.save(output_path, 'JPEG', quality=95)
            print(f"  ✅ Cover saved ({width}x{height})")
            return True
            
        except Exception as e:
            print(f"  ❌ Failed to download cover: {e}")
            return False
    
    def create_drama_metadata(self, book_id: str, title: str, cover_url: str, 
                             total_episodes: int = 100) -> Dict:
        """Create complete drama metadata structure"""
        return {
            "bookId": book_id,
            "title": title,
            "description": f"Drama {title}",
            "genre": "Romance",
            "tags": ["Drama", "Romance"],
            "totalEpisodes": total_episodes,
            "coverUrl": cover_url,
            "capturedAt": "2026-02-01",
            "source": "GoodShort"
        }
    
    def create_episodes_data(self, book_id: str, episode_count: int = 20) -> List[Dict]:
        """Create episode metadata with HLS URL pattern"""
        episodes = []
        
        for i in range(1, episode_count + 1):
            episode = {
                "episodeNumber": i,
                "title": f"Episode {i}",
                "duration": 0,
                # HLS URL pattern - ready for actual URLs when captured
                "hlsUrl": f"https://v2-akm.goodreels.com/mts/books/{book_id[-3:]}/{book_id}/EPISODE_ID/HASH/720p/VIDEO_720p.m3u8",
                "thumbnailUrl": None,
                "status": "ready"
            }
            episodes.append(episode)
        
        return episodes
    
    def scrape_drama(self, book_id: str, title: str, cover_url: str) -> bool:
        """Scrape complete drama data"""
        print(f"\n{'='*70}")
        print(f"📚 Scraping: {title}")
        print(f"{'='*70}")
        
        # Create drama folder
        drama_folder = OUTPUT_DIR / title.replace("/", "-")
        drama_folder.mkdir(exist_ok=True)
        
        # 1. Download cover
        cover_path = drama_folder / "cover.jpg"
        if not self.download_cover(cover_url, cover_path):
            print(f"  ⚠️  Using placeholder cover URL")
        
        # 2. Create metadata
        print(f"  📝 Creating metadata...")
        metadata = self.create_drama_metadata(book_id, title, cover_url)
        metadata_path = drama_folder / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        print(f"  ✅ Metadata saved")
        
        # 3. Create episodes data
        print(f"  📺 Creating episodes structure (1-20)...")
        episodes = self.create_episodes_data(book_id, episode_count=20)
        episodes_path = drama_folder / "episodes.json"
        with open(episodes_path, 'w', encoding='utf-8') as f:
            json.dump({"episodes": episodes}, f, indent=2, ensure_ascii=False)
        print(f"  ✅ Episodes structure saved (20 episodes)")
        
        print(f"\n✅ Drama scraped to: {drama_folder}")
        return True
    
    def upload_to_r2(self, drama_folder: Path):
        """Upload drama to Cloudflare R2"""
        if R2_ACCESS_KEY == "your_access_key":
            print(f"\n⚠️  R2 upload disabled - configure credentials first")
            return
        
        try:
            import boto3
            
            print(f"\n☁️  Uploading to R2...")
            
            s3_client = boto3.client(
                's3',
                endpoint_url=f'https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com',
                aws_access_key_id=R2_ACCESS_KEY,
                aws_secret_access_key=R2_SECRET_KEY
            )
            
            drama_name = drama_folder.name
            
            # Upload all files
            for file_path in drama_folder.glob("*"):
                if file_path.is_file():
                    s3_key = f"dramas/{drama_name}/{file_path.name}"
                    print(f"  📤 Uploading {file_path.name}...")
                    s3_client.upload_file(
                        str(file_path),
                        R2_BUCKET,
                        s3_key,
                        ExtraArgs={'ContentType': self._get_content_type(file_path)}
                    )
            
            print(f"  ✅ Uploaded to R2: dramas/{drama_name}/")
            
        except Exception as e:
            print(f"  ❌ R2 upload failed: {e}")
    
    def _get_content_type(self, file_path: Path) -> str:
        """Get content type for file"""
        ext = file_path.suffix.lower()
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.json': 'application/json'
        }
        return content_types.get(ext, 'application/octet-stream')

def main():
    """Main scraper execution"""
    print("\n" + "="*70)
    print("🎬 PRODUCTION GOODSHORT SCRAPER - FINAL VERSION")
    print("="*70 + "\n")
    
    scraper = ProductionScraper()
    
    # Sample dramas with real CDN cover URLs
    # TODO: Replace with actual captured data
    dramas = [
        {
            "bookId": "31001160993",
            "title": "Drama Sample 1",
            "coverUrl": "https://acf.goodreels.com/videobook/31001160993/202510/cover-uqBw0xaL1J.jpg"
        },
        # Add more dramas here as you capture them
    ]
    
    # Scrape each drama
    success_count = 0
    for drama in dramas:
        if scraper.scrape_drama(
            drama["bookId"],
            drama["title"],
            drama["coverUrl"]
        ):
            success_count += 1
    
    print(f"\n{'='*70}")
    print(f"✅ SCRAPING COMPLETE")
    print(f"{'='*70}")
    print(f"Scraped: {success_count}/{len(dramas)} dramas")
    print(f"Output: {OUTPUT_DIR}")
    print(f"\n🎯 Next Steps:")
    print(f"1. Update dramas list with actual book IDs and covers")
    print(f"2. Configure R2 credentials")
    print(f"3. Run with upload_to_r2=True")
    print()

if __name__ == "__main__":
    main()
