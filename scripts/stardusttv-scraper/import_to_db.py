#!/usr/bin/env python3
"""StardustTV Database Import"""

import json, psycopg2, os, uuid
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / 'backend' / '.env')

def gen_id():
    return str(uuid.uuid4()).replace('-', '')[:25]

def get_db():
    url = os.getenv('DATABASE_URL').split('?')[0]
    return psycopg2.connect(url)

def import_drama(conn, data):
    cur = conn.cursor()
    try:
        # Check existing
        cur.execute("SELECT id FROM \"Drama\" WHERE title = %s", (data['title'],))
        if cur.fetchone():
            print(f"   [SKIP] {data['title']}")
            return None
        
        # Insert drama
        drama_id = gen_id()
        cur.execute("""
            INSERT INTO "Drama" (id, title, description, cover, "totalEpisodes", country, language, "createdAt", "updatedAt")
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """, (drama_id, data['title'], data.get('description',''), data.get('coverUrl',''), 
              data.get('totalEpisodes',0), 'USA', 'English'))
        
        print(f"   [OK] {data['title']}")
        
        # Insert episodes
        count = 0
        for ep in data.get('episodes', []):
            if not ep.get('videoUrl'): continue
            cur.execute("""
                INSERT INTO "Episode" (id, "dramaId", "episodeNumber", title, "videoUrl", duration, "createdAt", "updatedAt")
                VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
            """, (gen_id(), drama_id, ep.get('episodeNumber',1), 
                  ep.get('title',''), ep.get('videoUrl',''), ep.get('duration',0)))
            count += 1
        
        print(f"      - {count} episodes imported")
        conn.commit()
        return drama_id
    except Exception as e:
        conn.rollback()
        print(f"   [ERROR] {e}")
        return None
    finally:
        cur.close()

def main():
    print("="*70)
    print("StardustTV Import")
    print("="*70 + "\n")
    
    files = list(Path("scraped_dramas").glob("*.json"))
    print(f"[INFO] Found {len(files)} file(s)\n")
    
    conn = get_db()
    imported = 0
    
    for f in files:
        print(f"[PROCESSING] {f.name}")
        with open(f) as file:
            if import_drama(conn, json.load(file)):
                imported += 1
    
    # Summary
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM \"Drama\"")
    total_d = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM \"Episode\"")
    total_e = cur.fetchone()[0]
    cur.close()
    conn.close()
    
    print(f"\n{'='*70}")
    print("[SUCCESS] IMPORT COMPLETE!")
    print(f"{'='*70}\n")
    print(f"Processed: {len(files)} | Imported: {imported}")
    print(f"Total DB: {total_d} dramas, {total_e} episodes\n")

if __name__ == '__main__':
    main()
