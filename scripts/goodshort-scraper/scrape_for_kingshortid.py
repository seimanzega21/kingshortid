#!/usr/bin/env python3
"""
KINGSHORTID-COMPATIBLE SCRAPER
==============================

Scrapes GoodShort dramas and outputs data in EXACT KingShortID database schema format.

Output Structure:
- dramas.json: Array of Drama objects matching Prisma schema
- episodes.json: Array of Episode objects matching Prisma schema
- import_metadata.json: Import statistics and mappings

Usage:
    python scrape_for_kingshortid.py
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import requests
from PIL import Image
from io import BytesIO

# Configuration
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR / "kingshortid_import"
OUTPUT_DIR.mkdir(exist_ok=True)

class KingShortIDScraper:
    """Scraper that outputs data matching KingShortID database schema"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        self.dramas = []
        self.episodes = []
        self.metadata = {
            "imported_at": datetime.now().isoformat(),
            "source": "GoodShort",
            "drama_count": 0,
            "episode_count": 0,
            "goodshort_mappings": {}  # bookId -> dramaId mapping
        }
    
    def generate_cuid(self, prefix: str = "") -> str:
        """Generate CUID-like ID for database"""
        import random
        import string
        timestamp = str(int(datetime.now().timestamp() * 1000))
        random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        return f"{prefix}{timestamp[-8:]}{random_part}"
    
    def parse_genre_string(self, genre_str: str) -> List[str]:
        """Convert GoodShort genre string to array"""
        if not genre_str:
            return ["Drama"]
        
        # Split by common separators
        genres = re.split(r'[,/]', genre_str)
        return [g.strip() for g in genres if g.strip()]
    
    def calculate_hls_duration(self, hls_url: str) -> int:
        """
        Calculate video duration from HLS playlist.
        Returns duration in seconds.
        """
        try:
            response = self.session.get(hls_url, timeout=10)
            response.raise_for_status()
            
            # Parse m3u8 playlist
            duration = 0
            for line in response.text.split('\n'):
                if line.startswith('#EXTINF:'):
                    # Extract duration from #EXTINF:5.005,
                    match = re.search(r'#EXTINF:([\d.]+)', line)
                    if match:
                        duration += float(match.group(1))
            
            return int(duration)
            
        except Exception as e:
            print(f"    ⚠️  Could not calculate duration: {e}")
            return 90  # Default 90 seconds for short dramas
    
    def download_cover(self, cover_url: str, output_path: Path) -> Optional[str]:
        """
        Download cover and return path.
        Returns local path or original URL if download fails.
        """
        try:
            response = self.session.get(cover_url, timeout=30)
            response.raise_for_status()
            
            # Validate image
            img = Image.open(BytesIO(response.content))
            width, height = img.size
            
            # Must be portrait
            if height <= width:
                print(f"    ⚠️  Not portrait, using URL only")
                return cover_url
            
            # Convert RGBA to RGB
            if img.mode == 'RGBA':
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[3])
                img = rgb_img
            
            # Save
            img.save(output_path, 'JPEG', quality=95)
            print(f"    ✅ Cover downloaded ({width}x{height})")
            return str(output_path)
            
        except Exception as e:
            print(f"    ⚠️  Cover download failed: {e}")
            return cover_url  # Return URL as fallback
    
    def create_drama(self, goodshort_data: Dict) -> Dict:
        """
        Create Drama object matching KingShortID Prisma schema.
        
        Schema:
        - id: String (cuid)
        - title: String
        - description: String
        - cover: String (URL or path)
        - banner: String? (optional)
        - genres: String[] (array)
        - tagList: String[] (array)
        - totalEpisodes: Int
        - rating: Float (default 0)
        - views: Int (default 0)
        - likes: Int (default 0)
        - reviewCount: Int (default 0)
        - averageRating: Float (default 0)
        - status: String (default "ongoing")
        - isVip: Boolean (default false)
        - isFeatured: Boolean (default false)
        - isActive: Boolean (default true)
        - ageRating: String (default "all")
        - releaseDate: DateTime? (optional)
        - director: String? (optional)
        - cast: String[] (array)
        - country: String (default "China")
        - language: String (default "Mandarin")
        - createdAt: DateTime
        - updatedAt: DateTime
        """
        drama_id = self.generate_cuid("drama_")
        
        # Download cover
        cover_path = OUTPUT_DIR / f"covers/{goodshort_data['bookId']}.jpg"
        cover_path.parent.mkdir(exist_ok=True)
        cover = self.download_cover(goodshort_data['coverUrl'], cover_path)
        
        drama = {
            # Primary fields
            "id": drama_id,
            "title": goodshort_data.get('title', 'Untitled Drama'),
            "description": goodshort_data.get('description', ''),
            "cover": cover,
            "banner": None,  # Not available in GoodShort
            
            # Categories
            "genres": self.parse_genre_string(goodshort_data.get('genre', 'Drama')),
            "tagList": goodshort_data.get('tags', []),
            
            # Stats
            "totalEpisodes": goodshort_data.get('totalEpisodes', 100),
            "rating": 0.0,
            "views": 0,
            "likes": 0,
            "reviewCount": 0,
            "averageRating": 0.0,
            
            # Status
            "status": "completed",  # Most GoodShort dramas are complete
            "isVip": False,
            "isFeatured": False,
            "isActive": True,
            "ageRating": "all",
            
            # Additional info
            "releaseDate": None,  # Not available
            "director": None,  # Not available
            "cast": [],  # Not available
            "country": "China",  # Default for GoodShort
            "language": "Mandarin",  # Default for GoodShort
            
            # Timestamps
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat(),
            
            # Metadata (for reference only, not in schema)
            "_metadata": {
                "goodshort_bookId": goodshort_data.get('bookId'),
                "goodshort_author": goodshort_data.get('author'),
                "source": "GoodShort"
            }
        }
        
        # Store mapping
        self.metadata["goodshort_mappings"][goodshort_data['bookId']] = drama_id
        
        return drama
    
    def create_episode(self, drama_id: str, goodshort_episode: Dict, 
                      calculate_duration: bool = True) -> Dict:
        """
        Create Episode object matching KingShortID Prisma schema.
        
        Schema:
        - id: String (cuid)
        - dramaId: String (foreign key)
        - episodeNumber: Int
        - title: String
        - description: String? (optional)
        - thumbnail: String? (optional)
        - videoUrl: String (HLS URL)
        - duration: Int (seconds)
        - isVip: Boolean (default false)
        - coinPrice: Int (default 0)
        - views: Int (default 0)
        - isActive: Boolean (default true)
        - releaseDate: DateTime
        - createdAt: DateTime
        - updatedAt: DateTime
        - seasonId: String? (optional)
        """
        episode_id = self.generate_cuid("episode_")
        
        # Calculate duration from HLS if available
        duration = 90  # Default
        if calculate_duration and goodshort_episode.get('hlsUrl'):
            print(f"    📊 Calculating duration for Episode {goodshort_episode['episodeNumber']}...")
            duration = self.calculate_hls_duration(goodshort_episode['hlsUrl'])
        
        episode = {
            # Primary fields
            "id": episode_id,
            "dramaId": drama_id,
            
            # Episode info
            "episodeNumber": goodshort_episode.get('episodeNumber', 1),
            "title": goodshort_episode.get('title', f"Episode {goodshort_episode.get('episodeNumber', 1)}"),
            "description": None,  # Not available in GoodShort
            "thumbnail": None,  # Not available in GoodShort
            
            # Video
            "videoUrl": goodshort_episode.get('hlsUrl', ''),
            "duration": duration,
            
            # Access control
            "isVip": False,  # Default free
            "coinPrice": 0,  # Default free
            
            # Stats
            "views": 0,
            
            # Status
            "isActive": True,
            "releaseDate": datetime.now().isoformat(),
            
            # Timestamps
            "createdAt": datetime.now().isoformat(),
            "updatedAt": datetime.now().isoformat(),
            
            # Organization
            "seasonId": None,  # Not using seasons for now
            
            # Metadata (for reference only)
            "_metadata": {
                "goodshort_episodeId": goodshort_episode.get('episodeId'),
                "source": "GoodShort"
            }
        }
        
        return episode
    
    def import_drama(self, goodshort_data: Dict, episodes_data: List[Dict],
                    calculate_duration: bool = True) -> Dict:
        """
        Import complete drama with episodes.
        Returns drama object with metadata.
        """
        print(f"\n{'='*70}")
        print(f"📚 Importing: {goodshort_data.get('title', 'Unknown')}")
        print(f"{'='*70}")
        
        # Create drama
        print(f"  📝 Creating drama record...")
        drama = self.create_drama(goodshort_data)
        self.dramas.append(drama)
        print(f"  ✅ Drama created: {drama['id']}")
        
        # Create episodes
        print(f"  📺 Creating {len(episodes_data)} episodes...")
        for ep_data in episodes_data:
            episode = self.create_episode(
                drama['id'], 
                ep_data,
                calculate_duration=calculate_duration
            )
            self.episodes.append(episode)
        
        print(f"  ✅ {len(episodes_data)} episodes created")
        
        return drama
    
    def save_output(self):
        """Save all data to JSON files"""
        print(f"\n{'='*70}")
        print(f"💾 Saving output...")
        print(f"{'='*70}")
        
        # Update metadata
        self.metadata["drama_count"] = len(self.dramas)
        self.metadata["episode_count"] = len(self.episodes)
        
        # Save dramas
        dramas_file = OUTPUT_DIR / "dramas.json"
        with open(dramas_file, 'w', encoding='utf-8') as f:
            json.dump(self.dramas, f, indent=2, ensure_ascii=False)
        print(f"  ✅ Saved {len(self.dramas)} dramas to: {dramas_file}")
        
        # Save episodes
        episodes_file = OUTPUT_DIR / "episodes.json"
        with open(episodes_file, 'w', encoding='utf-8') as f:
            json.dump(self.episodes, f, indent=2, ensure_ascii=False)
        print(f"  ✅ Saved {len(self.episodes)} episodes to: {episodes_file}")
        
        # Save metadata
        metadata_file = OUTPUT_DIR / "import_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        print(f"  ✅ Saved import metadata to: {metadata_file}")
        
        print(f"\n📊 Import Statistics:")
        print(f"  - Dramas: {self.metadata['drama_count']}")
        print(f"  - Episodes: {self.metadata['episode_count']}")
        print(f"  - Output: {OUTPUT_DIR}")

def main():
    """Main execution"""
    print("\n" + "="*70)
    print("🎬 KINGSHORTID-COMPATIBLE SCRAPER")
    print("="*70 + "\n")
    
    scraper = KingShortIDScraper()
    
    # Load existing scraped data
    scraped_dir = SCRIPT_DIR / "scraped_dramas"
    
    if not scraped_dir.exists():
        print("❌ No scraped_dramas folder found!")
        print("Please run the GoodShort scraper first.")
        return
    
    # Import each drama
    for drama_folder in scraped_dir.iterdir():
        if not drama_folder.is_dir():
            continue
        
        metadata_file = drama_folder / "metadata.json"
        episodes_file = drama_folder / "episodes.json"
        
        if not metadata_file.exists() or not episodes_file.exists():
            print(f"⚠️  Skipping {drama_folder.name} - missing files")
            continue
        
        # Load data
        with open(metadata_file, 'r', encoding='utf-8') as f:
            drama_data = json.load(f)
        
        with open(episodes_file, 'r', encoding='utf-8') as f:
            episodes_data = json.load(f)
            if isinstance(episodes_data, dict) and 'episodes' in episodes_data:
                episodes_data = episodes_data['episodes']
        
        # Import (skip duration calculation for speed, can add later)
        scraper.import_drama(drama_data, episodes_data, calculate_duration=False)
    
    # Save all output
    scraper.save_output()
    
    print(f"\n{'='*70}")
    print(f"✅ IMPORT COMPLETE!")
    print(f"{'='*70}")
    print(f"\n🎯 Next Steps:")
    print(f"1. Review: {OUTPUT_DIR}/dramas.json")
    print(f"2. Review: {OUTPUT_DIR}/episodes.json")
    print(f"3. Import to database using Prisma client")
    print()

if __name__ == "__main__":
    main()
