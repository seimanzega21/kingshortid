#!/usr/bin/env python3
"""
DATABASE IMPORTER - Import GoodShort Data to PostgreSQL
======================================================

Imports scraped GoodShort drama metadata and episodes from r2_ready/ 
folder into the KingShortID PostgreSQL database via Prisma.

Usage:
    python import_to_database.py
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SCRIPT_DIR = Path(__file__).parent
SOURCE_DIR = SCRIPT_DIR / "r2_ready"
R2_PUBLIC_URL = os.getenv("R2_PUBLIC_URL", "https://stream.shortlovers.id")

# Parse DATABASE_URL and remove Prisma-specific parameters
raw_db_url = os.getenv("DATABASE_URL", "")
if "?schema=" in raw_db_url:
    DATABASE_URL = raw_db_url.split("?")[0]  # Remove Prisma schema param
else:
    DATABASE_URL = raw_db_url

class DatabaseImporter:
    """Import GoodShort data to PostgreSQL database"""
    
    def __init__(self):
        self.imported_dramas = []
        self.imported_episodes = 0
        self.skipped_dramas = []
        
        # Parse database URL
        if not DATABASE_URL:
            raise ValueError("DATABASE_URL not found in environment")
        
        # Connect to database
        self.conn = psycopg2.connect(DATABASE_URL)
        self.cursor = self.conn.cursor()
    
    def __del__(self):
        """Close database connection"""
        if hasattr(self, 'cursor') and self.cursor:
            self.cursor.close()
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
    
    def drama_exists(self, book_id: str) -> bool:
        """Check if drama already exists by bookId in description"""
        self.cursor.execute(
            "SELECT id FROM \"Drama\" WHERE description LIKE %s LIMIT 1",
            (f'%{book_id}%',)
        )
        return self.cursor.fetchone() is not None
    
    def import_drama(self, drama_folder: Path, metadata: Dict) -> str:
        """Import drama and its episodes"""
        book_id = metadata.get('bookId', '')
        title = metadata.get('title', 'Untitled')
        description = metadata.get('description', '')
        cover_url = metadata.get('cover', '')
        total_episodes = metadata.get('total_episodes', 0)
        episodes_data = metadata.get('episodes', [])
        
        # Use folder name for drama folder path (e.g., "Cinta_di_Waktu_yang_Tepat")
        drama_folder_name = drama_folder.name
        
        # Construct R2 URLs
        r2_cover_url = f"{R2_PUBLIC_URL}/{drama_folder_name}/cover.jpg"
        
        print(f"\\n  📝 Importing: {title}")
        print(f"     Book ID: {book_id}")
        print(f"     Episodes: {total_episodes}")
        
        # Check if already exists
        if self.drama_exists(book_id):
            print(f"     ⚠️  Already exists, skipping...")
            self.skipped_dramas.append(title)
            return None
        
        # Insert drama
        self.cursor.execute("""
            INSERT INTO "Drama" (
                id, title, description, cover, banner,
                genres, "tagList", "totalEpisodes",
                rating, views, likes,
                status, "isVip", "isFeatured", "isActive",
                country, language,
                "createdAt", "updatedAt"
            ) VALUES (
                gen_random_uuid(), %s, %s, %s, %s,
                %s, %s, %s,
                0, 0, 0,
                'completed', false, false, true,
                'Indonesia', 'Indonesian',
                NOW(), NOW()
            ) RETURNING id
        """, (
            title,
            f"{description}\\n\\n[BookID: {book_id}]",  # Store bookId in description for tracking
            r2_cover_url,
            r2_cover_url,  # Use cover as banner too
            ['Romance', 'Drama'],  # Default genres, will be enriched later
            ['GoodShort', 'Indonesian'],  # Tags
            total_episodes
        ))
        
        drama_id = self.cursor.fetchone()[0]
        print(f"     ✅ Drama created: {drama_id}")
        
        # Import episodes (with proper error handling)
        episode_count = 0
        for ep_data in episodes_data:
            # Skip episodes without video URL
            if not ep_data.get('video_url'):
                continue
            
            episode_index = ep_data.get('index', 0)
            episode_number = episode_index + 1  # Convert 0-based to 1-based
            chapter_name = ep_data.get('chapterName', f'{episode_number:03d}')
            play_time = ep_data.get('playTime', 0)
            
            # Construct R2 video URL (M3U8 playlist)
            r2_video_url = f"{R2_PUBLIC_URL}/{drama_folder_name}/episode_{episode_index:03d}/playlist.m3u8"
            
            # Insert episode (skip if duplicate, don't rollback entire transaction)
            try:
                self.cursor.execute("""
                    INSERT INTO "Episode" (
                        id, "dramaId", "episodeNumber", title,
                        description, thumbnail, "videoUrl", duration,
                        "isVip", "coinPrice", views,
                        "isActive", "releaseDate",
                        "createdAt", "updatedAt"
                    ) VALUES (
                        gen_random_uuid(), %s, %s, %s,
                        %s, %s, %s, %s,
                        false, 0, 0,
                        true, NOW(),
                        NOW(), NOW()
                    )
                """, (
                    drama_id,
                    episode_number,
                    f"Episode {chapter_name}",
                    f"",  # No description
                    r2_cover_url,  # Use drama cover as episode thumbnail
                    r2_video_url,
                    play_time
                ))
                episode_count += 1
            except psycopg2.IntegrityError as e:
                # Episode duplicate - just skip, don't rollback
                print(f"       ⚠️  Episode {episode_number} already exists, skipping...")
                continue
        
        # Commit AFTER all episodes processed
        self.conn.commit()
        print(f"     ✅ Imported {episode_count} episodes")
        
        self.imported_episodes += episode_count
        self.imported_dramas.append(title)
        
        return drama_id
    
    def import_all(self):
        """Import all dramas from r2_ready folder"""
        if not SOURCE_DIR.exists():
            print(f"❌ Source directory not found: {SOURCE_DIR}")
            print(f"Run scraper scripts first to populate r2_ready/")
            return
        
        # Find all drama folders
        drama_folders = [f for f in SOURCE_DIR.iterdir() if f.is_dir()]
        
        if not drama_folders:
            print(f"❌ No drama folders found in {SOURCE_DIR}")
            return
        
        print(f"✅ Found {len(drama_folders)} dramas to import\\n")
        
        # Import each drama
        for i, folder in enumerate(drama_folders, 1):
            print(f"{'='*70}")
            print(f"📥 Processing {i}/{len(drama_folders)}: {folder.name}")
            print(f"{'='*70}")
            
            # Read metadata.json
            metadata_file = folder / "metadata.json"
            if not metadata_file.exists():
                print(f"  ⚠️  metadata.json not found, skipping...")
                self.skipped_dramas.append(folder.name)
                continue
            
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                self.import_drama(folder, metadata)
            
            except Exception as e:
                print(f"  ❌ Import failed: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                self.skipped_dramas.append(folder.name)
        
        # Summary
        print(f"\\n{'='*70}")
        print(f"✅ DATABASE IMPORT COMPLETE!")
        print(f"{'='*70}")
        print(f"\\n📊 Statistics:")
        print(f"  - Dramas imported: {len(self.imported_dramas)}")
        print(f"  - Episodes imported: {self.imported_episodes}")
        print(f"  - Dramas skipped: {len(self.skipped_dramas)}")
        
        if self.imported_dramas:
            print(f"\\n✅ Imported Dramas:")
            for drama in self.imported_dramas:
                print(f"  - {drama}")
        
        if self.skipped_dramas:
            print(f"\\n⚠️  Skipped:")
            for drama in self.skipped_dramas:
                print(f"  - {drama}")
        
        print(f"\\n🎉 Ready to test in KingShortID app!\\n")

def check_database():
    """Check if database is accessible"""
    if not DATABASE_URL:
        print("❌ DATABASE_URL not configured!")
        print("\\nPlease set in .env file:")
        print("DATABASE_URL=postgresql://user:pass@localhost:5432/kingshort")
        return False
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def main():
    print("\\n" + "="*70)
    print("📦 DATABASE IMPORTER - GoodShort to PostgreSQL")
    print("="*70 + "\\n")
    
    # Check database
    if not check_database():
        return
    
    print("✅ Database connection OK\\n")
    
    try:
        importer = DatabaseImporter()
        importer.import_all()
    except KeyboardInterrupt:
        print("\\n\\n⚠️  Import cancelled by user")
    except Exception as e:
        print(f"\\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
