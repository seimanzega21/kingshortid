"""Import with fresh connection per drama"""
import psycopg2
import json
from pathlib import Path

DATABASE_URL = "postgresql://postgres:seiman21@localhost:5432/kingshort"
R2_PUBLIC_URL = "https://stream.shortlovers.id"
SOURCE_DIR = Path("D:/kingshortid/scripts/goodshort-scraper/r2_ready")

def import_drama(drama_folder):
    """Import single drama with fresh connection"""
    
    # Fresh connection for this drama
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    try:
        metadata_file = drama_folder / "metadata.json"
        if not metadata_file.exists():
            print(f"⚠️  Skipping {drama_folder.name} - no metadata.json\n")
            return False
        
        print(f"="*70)
        print(f"📥 Processing: {drama_folder.name}")
        print(f"="*70)
        
        # Load metadata
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        book_id = metadata['bookId']
        title = metadata['title']
        description = metadata.get('description', '')
        total_episodes = metadata['total_episodes']
        episodes_data = metadata['episodes']
        
        print(f"Title: {title}")
        print(f"BookID: {book_id}")
        print(f"Total Episodes: {total_episodes}")
        
        # Check if exists
        cur.execute('SELECT id FROM "Drama" WHERE description LIKE %s LIMIT 1', (f'%{book_id}%',))
        if cur.fetchone():
            print(f"⚠️  Already exists, skipping...\n")
            return False
        
        # Insert drama
        r2_cover_url = f"{R2_PUBLIC_URL}/{drama_folder.name}/cover.jpg"
        
        cur.execute("""
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
            f"{description}\n\n[BookID: {book_id}]",
            r2_cover_url,
            r2_cover_url,
            ['Romance', 'Drama'],
            ['GoodShort', 'Indonesian'],
            total_episodes
        ))
        
        drama_id = cur.fetchone()[0]
        print(f"✅ Drama inserted: {drama_id}")
        
        # Insert episodes
        episode_count = 0
        for ep_data in episodes_data:
            if not ep_data.get('video_url'):
                continue
            
            episode_index = ep_data.get('index', 0)
            episode_number = episode_index + 1
            chapter_name = ep_data.get('chapterName', f'{episode_number:03d}')
            play_time = ep_data.get('playTime', 0)
            
            r2_video_url = f"{R2_PUBLIC_URL}/{drama_folder.name}/episode_{episode_index:03d}/playlist.m3u8"
            
            cur.execute("""
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
                "",
                r2_cover_url,
                r2_video_url,
                play_time
            ))
            episode_count += 1
        
        conn.commit()
        print(f"✅ Imported {episode_count} episodes\n")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

# Main import
print("✅ Starting import with fresh connections\n")

imported = 0
skipped = 0

for drama_folder in SOURCE_DIR.iterdir():
    if not drama_folder.is_dir():
        continue
    
    if import_drama(drama_folder):
        imported += 1
    else:
        skipped += 1

print("="*70)
print("🎉 IMPORT COMPLETE!")
print(f"   Imported: {imported}")
print(f"   Skipped: {skipped}")
print("="*70)
