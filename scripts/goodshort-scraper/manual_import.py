#!/usr/bin/env python3
"""Manual import with detailed logging"""

import json
import psycopg2
from pathlib import Path

# Database connection
DATABASE_URL = "postgresql://postgres:seiman21@localhost:5432/kingshort"
R2_PUBLIC_URL = "https://stream.shortlovers.id"
SOURCE_DIR = Path("D:/kingshortid/scripts/goodshort-scraper/r2_ready")

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    print("✅ Connected to database\n")
    
    # Import Cinta di Waktu yang Tepat
    metadata_file = SOURCE_DIR / "Cinta_di_Waktu_yang_Tepat" / "metadata.json"
    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)
    
    title = metadata['title']
    book_id = metadata['bookId']
    description = metadata.get('description', '')
    total_episodes = metadata['total_episodes']
    episodes_data = metadata['episodes']
    
    drama_folder_name = "Cinta_di_Waktu_yang_Tepat"
    r2_cover_url = f"{R2_PUBLIC_URL}/goodshort/{drama_folder_name}/cover.jpg"
    
    print(f"📥 Importing: {title}")
    print(f"   BookID: {book_id}")
    print(f"   Total Episodes: {total_episodes}")
    print(f"   Episodes with video_url: {sum(1 for e in episodes_data if e.get('video_url'))}\n")
    
    # Insert drama
    try:
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
        print(f"✅ Drama inserted with ID: {drama_id}")
        
        # Insert episodes
        episode_count = 0
        for ep_data in episodes_data:
            if not ep_data.get('video_url'):
                continue
            
            episode_index = ep_data.get('index', 0)
            episode_number = episode_index + 1
            chapter_name = ep_data.get('chapterName', f'{episode_number:03d}')
            play_time = ep_data.get('playTime', 0)
            
            r2_video_url = f"{R2_PUBLIC_URL}/goodshort/{drama_folder_name}/episode_{episode_index:03d}/video.m3u8"
            
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
        print(f"✅ Imported {episode_count} episodes")
        print(f"✅ COMMITTED TO DATABASE!\n")
        
    except Exception as e:
        print(f"❌ Error inserting drama: {e}")
        conn.rollback()
        raise
    
    # Now import Hidup Kedua
    metadata_file2 = SOURCE_DIR / "Hidup_Kedua,_Cinta_Sejati_Menanti" / "metadata.json"
    with open(metadata_file2, 'r', encoding='utf-8') as f:
        metadata2 = json.load(f)
    
    title2 = metadata2['title']
    book_id2 = metadata2['bookId']
    description2 = metadata2.get('description', '')
    total_episodes2 = metadata2['total_episodes']
    episodes_data2 = metadata2['episodes']
    
    drama_folder_name2 = "Hidup_Kedua,_Cinta_Sejati_Menanti"
    r2_cover_url2 = f"{R2_PUBLIC_URL}/goodshort/{drama_folder_name2}/cover.jpg"
    
    print(f"📥 Importing: {title2}")
    print(f"   BookID: {book_id2}")
    print(f"   Total Episodes: {total_episodes2}")
    print(f"   Episodes with video_url: {sum(1 for e in episodes_data2 if e.get('video_url'))}\n")
    
    try:
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
            title2,
            f"{description2}\n\n[BookID: {book_id2}]",
            r2_cover_url2,
            r2_cover_url2,
            ['Romance', 'Drama'],
            ['GoodShort', 'Indonesian'],
            total_episodes2
        ))
        
        drama_id2 = cur.fetchone()[0]
        print(f"✅ Drama inserted with ID: {drama_id2}")
        
        episode_count2 = 0
        for ep_data in episodes_data2:
            if not ep_data.get('video_url'):
                continue
            
            episode_index = ep_data.get('index', 0)
            episode_number = episode_index + 1
            chapter_name = ep_data.get('chapterName', f'{episode_number:03d}')
            play_time = ep_data.get('playTime', 0)
            
            r2_video_url = f"{R2_PUBLIC_URL}/goodshort/{drama_folder_name2}/episode_{episode_index:03d}/video.m3u8"
            
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
                drama_id2,
                episode_number,
                f"Episode {chapter_name}",
                "",
                r2_cover_url2,
                r2_video_url,
                play_time
            ))
            episode_count2 += 1
        
        conn.commit()
        print(f"✅ Imported {episode_count2} episodes")
        print(f"✅ COMMITTED TO DATABASE!\n")
        
    except Exception as e:
        print(f"❌ Error inserting drama 2: {e}")
        conn.rollback()
        raise
    
    print("="*70)
    print("🎉 IMPORT COMPLETE!")
    print(f"   Total dramas: 2")
    print(f"   Total episodes: {episode_count + episode_count2}")
    print("="*70)
    
except Exception as e:
    print(f"\n❌ FATAL ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    if 'cur' in locals():
        cur.close()
    if 'conn' in locals():
        conn.close()
