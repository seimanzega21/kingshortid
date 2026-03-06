import psycopg2, os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
load_dotenv(Path(__file__).parent.parent / 'backend' / '.env')

conn = psycopg2.connect(os.getenv('DATABASE_URL').split('?')[0])
cur = conn.cursor()

# Check for any remaining generic descriptions
cur.execute("""
    SELECT title, description FROM "Drama" 
    WHERE "isActive" = true 
    AND (description LIKE 'Drama pendek:%' OR description IS NULL OR LENGTH(description) < 20)
    ORDER BY title
""")
rows = cur.fetchall()
if rows:
    print(f"Dramas with bad descriptions ({len(rows)}):")
    for r in rows:
        print(f"  {r[0]}: '{r[1] or 'NULL'}'")
else:
    print("All descriptions are good!")

# Verify Mata Kiri
cur.execute("""SELECT title, description FROM "Drama" WHERE title = 'Mata Kiri Ajaibku' AND "isActive" = true""")
r = cur.fetchone()
print(f"\nMata Kiri Ajaibku desc: {r[1]}")

cur.close()
conn.close()
