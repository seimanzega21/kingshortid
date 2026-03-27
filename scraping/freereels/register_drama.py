"""Register new drama + check existing ones"""
import psycopg2, sys, json, uuid
from datetime import datetime
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

conn = psycopg2.connect('postgresql://postgres:seiman21@localhost:5432/kingshort')
cur = conn.cursor()

# Check existing FreeReels dramas
cur.execute("""SELECT id, title, substring(description from '\\[FRkey:([^\\]]+)\\]') as frkey 
               FROM "Drama" WHERE description LIKE '%[FRkey:%' ORDER BY title""")
existing = cur.fetchall()
print(f'Existing FreeReels dramas: {len(existing)}')
for r in existing:
    print(f'  {r[0]}: {r[1]} (FRkey:{r[2]})')

# Check if 'eNFDnztZRb' exists
target_key = 'eNFDnztZRb'
found = [r for r in existing if r[2] == target_key]
if found:
    print(f'\nDrama with FRkey:{target_key} already exists: {found[0][1]}')
else:
    print(f'\nDrama with FRkey:{target_key} NOT found. Creating...')
    drama_id = str(uuid.uuid4())
    cur.execute("""
        INSERT INTO "Drama" (id, title, description, cover, "totalEpisodes", 
                            "isActive", "createdAt", "updatedAt")
        VALUES (%s, %s, %s, %s, %s, false, NOW(), NOW())
        RETURNING id
    """, (drama_id, 'Bos Kuliah Lagi (Sulih Suara)', 
          'Drama pendek tentang kehidupan kampus. Audio Indonesia (Sulih Suara). [FRkey:eNFDnztZRb]',
          '', 87))
    conn.commit()
    print(f'  Created drama: {drama_id}')

conn.close()
