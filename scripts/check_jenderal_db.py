import psycopg2, os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / 'backend' / '.env')

url = os.getenv('DATABASE_URL').split('?')[0]
conn = psycopg2.connect(url)
cur = conn.cursor()

# Find ALL dramas matching jenderal or 09750069
cur.execute("""SELECT id, title, cover FROM "Drama" WHERE title ILIKE '%%jenderal%%' OR title ILIKE '%%09750069%%' OR cover ILIKE '%%09750069%%'""")
rows = cur.fetchall()

print(f"Found {len(rows)} matching dramas:")
for r in rows:
    print(f"  ID: {r[0]}")
    print(f"  Title: {r[1]}")
    print(f"  Cover: {r[2]}")
    print()

# Also check for drama-09750069 in cover URLs
cur.execute("""SELECT id, title, cover FROM "Drama" WHERE cover ILIKE '%%drama-09750069%%'""")
rows2 = cur.fetchall()
print(f"\nDramas with old cover URL (drama-09750069): {len(rows2)}")
for r in rows2:
    print(f"  ID: {r[0]}, Title: {r[1]}, Cover: {r[2]}")

cur.close()
conn.close()
