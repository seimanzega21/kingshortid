import psycopg2, os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / 'backend' / '.env')

url = os.getenv('DATABASE_URL').split('?')[0]
conn = psycopg2.connect(url)
cur = conn.cursor()

# Find Jenderal Terakhir
cur.execute("""SELECT id, title FROM "Drama" WHERE title = 'Jenderal Terakhir'""")
row = cur.fetchone()
if not row:
    print("Drama not found!")
    exit()

drama_id = row[0]
print(f"Drama: {row[1]} (ID: {drama_id})")

# Check current episode URLs
cur.execute("""SELECT id, "episodeNumber", "videoUrl" FROM "Episode" WHERE "dramaId" = %s ORDER BY "episodeNumber" LIMIT 3""", (drama_id,))
eps = cur.fetchall()
print(f"\nCurrent URLs (sample):")
for e in eps:
    print(f"  Ep {e[1]}: {e[2]}")

# Fix: replace drama-09750069 with jenderal-terakhir in all episode URLs
cur.execute("""
    UPDATE "Episode" 
    SET "videoUrl" = REPLACE("videoUrl", 'drama-09750069', 'jenderal-terakhir')
    WHERE "dramaId" = %s AND "videoUrl" LIKE '%%drama-09750069%%'
""", (drama_id,))
updated = cur.rowcount
conn.commit()
print(f"\nUpdated {updated} episode URLs")

# Verify
cur.execute("""SELECT "episodeNumber", "videoUrl" FROM "Episode" WHERE "dramaId" = %s ORDER BY "episodeNumber" LIMIT 3""", (drama_id,))
for e in cur.fetchall():
    print(f"  Ep {e[0]}: {e[1]}")

cur.close()
conn.close()
print("\nDone!")
