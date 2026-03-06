import psycopg2, os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
load_dotenv(Path(__file__).parent.parent / 'backend' / '.env')

conn = psycopg2.connect(os.getenv('DATABASE_URL').split('?')[0])
cur = conn.cursor()

# The deactivated drama's TITLE is the actual description
cur.execute("""SELECT title FROM "Drama" WHERE title ILIKE '%Erick Breno%'""")
row = cur.fetchone()
if row:
    full_title = row[0]
    print(f"Deactivated title (= real description): {full_title}")
    
    # Update Mata Kiri Ajaibku with this as description
    cur.execute("""UPDATE "Drama" SET description = %s WHERE title = 'Mata Kiri Ajaibku' AND "isActive" = true""", (full_title,))
    conn.commit()
    print(f"\n✅ Updated!")

# Also check if there are other dramas with generic "Drama pendek: ..." descriptions
cur.execute("""SELECT id, title, description FROM "Drama" WHERE "isActive" = true AND description LIKE 'Drama pendek:%'""")
generic = cur.fetchall()
if generic:
    print(f"\n⚠️  Other dramas with generic descriptions:")
    for r in generic:
        print(f"  {r[1]}: {r[2]}")

# Verify
cur.execute("""SELECT title, description FROM "Drama" WHERE title = 'Mata Kiri Ajaibku' AND "isActive" = true""")
r = cur.fetchone()
print(f"\nVerified: {r[0]}")
print(f"  New desc: {r[1]}")

cur.close()
conn.close()
