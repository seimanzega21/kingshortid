"""Direct import - no exception handling, commit per episode batch"""
import psycopg2
import json
from pathlib import Path

DATABASE_URL = "postgresql://postgres:seiman21@localhost:5432/kingshort"
R2_PUBLIC_URL = "https://stream.shortlovers.id"
SOURCE_DIR = Path("D:/kingshortid/scripts/goodshort-scraper/r2_ready")

conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = False
cur = conn.cursor()

print("✅ Connected\n")

for drama_folder in SOURCE_DIR.iterdir():
    if not drama_folder.is_dir():
        continue
    
    metadata_file = drama_folder / "metadata.json"
    if not metadata_file.exists():
        continue
    
    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    book_id = metadata['bookId']
    title = metadata['title']
    description = metadata.get('description', '')
    total_episodes = metadata['total_episodes']
    episodes_data = metadata['episodes']
    
    print(f"Processing: {title}")
    
    # Check exists
    cur.execute('SELECT id FROM "Drama" WHERE description LIKE %s', (f'%{book_id}%',))
    if cur.fetchone():
        print("  Already exists, skipping\n")
        continue
    
    # Insert drama
    r2_cover = f"{R2_PUBLIC_URL}/{drama_folder.name}/cover.jpg"
    
    cur.execute("""
        INSERT INTO "Drama" (
            id, title, description, cover, banner,
            genres, "tagList", "totalEpisodes",
            rating, views, likes, status, "isVip", "isFeatured", "isActive",
            country, language, "createdAt", "updatedAt"
        ) VALUES (
            gen_random_uuid(), %s, %s, %s, %s,
            %s, %s, %s,
            0, 0, 0, 'completed', false, false, true,
            'Indonesia', 'Indonesian', NOW(), NOW()
        ) RETURNING id
    """, (
        title, f"{description}\n\n[BookID: {book_id}]",
        r2_cover, r2_cover,
        ['Romance', 'Drama'], ['GoodShort', 'Indonesian'],
        total_episodes
    ))
    
    drama_id = cur.fetchone()[0]
    print(f"  Drama ID: {drama_id}")
    
    # Commit drama immediately
    conn.commit()
    print("  ✅ Drama committed")
    
    # Insert episodes in batches
    ep_count = 0
    for ep_data in episodes_data:
        if not ep_data.get('video_url'):
            continue
        
        episode_index = ep_data.get('index', 0)
        episode_number = episode_index + 1
        chapter_name = ep_data.get('chapterName', f'{episode_number:03d}')
        play_time = ep_data.get('playTime', 0)
        
        r2_video = f"{R2_PUBLIC_URL}/{drama_folder.name}/episode_{episode_index:03d}/playlist.m3u8"
        
        # Check if episode exists first
        cur.execute(
            'SELECT id FROM "Episode" WHERE "dramaId" = %s AND "episodeNumber" = %s',
            (drama_id, episode_number)
        )
        
        if cur.fetchone():
            continue  # Skip duplicate
        
        cur.execute("""
            INSERT INTO "Episode" (
                id, "dramaId", "episodeNumber", title,
                description, thumbnail, "videoUrl", duration,
                "isVip", "coinPrice", views, "isActive", "releaseDate",
                "createdAt", "updatedAt"
            ) VALUES (
                gen_random_uuid(), %s, %s, %s,
                %s, %s, %s, %s,
                false, 0, 0, true, NOW(),
                NOW(), NOW()
            )
        """, (
            drama_id, episode_number, f"Episode {chapter_name}",
            "", r2_cover, r2_video, play_time
        ))
        
        ep_count += 1
        
        # Commit every 10 episodes
        if ep_count % 10 == 0:
            conn.commit()
    
    # Final commit for remaining episodes
    conn.commit()
    print(f"  ✅ Imported {ep_count} episodes\n")

cur.close()
conn.close()

print("🎉 DONE!")
