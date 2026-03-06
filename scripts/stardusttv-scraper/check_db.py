#!/usr/bin/env python3
"""Quick check for StardustTV dramas in database"""
import psycopg2
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv(Path(__file__).parent.parent.parent / 'backend' / '.env')

conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cursor = conn.cursor()

# Get StardustTV dramas
cursor.execute("""
    SELECT d.id, d.title, d.source, d."totalEpisodes", 
           (SELECT COUNT(*) FROM "Episode" WHERE "dramaId" = d.id) as actual_episodes
    FROM "Drama" d
    WHERE d.source = 'stardusttv'
""")

dramas = cursor.fetchall()

print("\n" + "="*70)
print("STARDUSTTV DRAMAS IN DATABASE")
print("="*70)

if dramas:
    for drama in dramas:
        print(f"\n[{drama[0]}] {drama[1]}")
        print(f"   Source: {drama[2]}")
        print(f"   Total Episodes: {drama[3]}")
        print(f"   Episodes in DB: {drama[4]}")
else:
    print("\n[WARN] No StardustTV dramas found in database!")

# Get total counts
cursor.execute("SELECT COUNT(*) FROM \"Drama\"")
total_dramas = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM \"Episode\"")
total_episodes = cursor.fetchone()[0]

print("\n" + "="*70)
print(f"TOTAL: {total_dramas} dramas, {total_episodes} episodes")
print("="*70 + "\n")

cursor.close()
conn.close()
