import psycopg2, os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / 'backend' / '.env')

url = os.getenv('DATABASE_URL').split('?')[0]
conn = psycopg2.connect(url)
cur = conn.cursor()

# 1. Find ALL Jenderal dramas with episode count
print("=== All Jenderal dramas with episode counts ===\n")
cur.execute("""
    SELECT d.id, d.title, d.cover, d."totalEpisodes",
           (SELECT COUNT(*) FROM "Episode" WHERE "dramaId" = d.id) as ep_count
    FROM "Drama" d 
    WHERE d.title ILIKE '%%jenderal%%'
    ORDER BY d.title, d."createdAt"
""")
rows = cur.fetchall()
for r in rows:
    print(f"ID: {r[0]}")
    print(f"  Title: {r[1]}")
    print(f"  Cover: {r[2]}")
    print(f"  Total: {r[3]}, Episodes in DB: {r[4]}")
    print()

# 2. Keep only the Jenderal Terakhir with most episodes, delete rest
jt_dramas = [r for r in rows if r[1] == 'Jenderal Terakhir']
if len(jt_dramas) > 1:
    # Keep the one with most episodes
    best = max(jt_dramas, key=lambda x: x[4])
    print(f"Keeping: {best[0]} ({best[4]} episodes)")
    
    for r in jt_dramas:
        if r[0] != best[0]:
            print(f"Deleting duplicate: {r[0]} ({r[4]} episodes)")
            cur.execute('DELETE FROM "Episode" WHERE "dramaId" = %s', (r[0],))
            cur.execute('DELETE FROM "Drama" WHERE id = %s', (r[0],))
    
    conn.commit()
    print("Duplicates removed!")

# 3. Update cover for remaining Jenderal Terakhir
cover_url = 'https://stream.shortlovers.id/melolo/jenderal-terakhir/cover.jpg'
cur.execute("""UPDATE "Drama" SET cover = %s WHERE title = 'Jenderal Terakhir'""", (cover_url,))
conn.commit()
print(f"\nCover updated to: {cover_url}")

# 4. Final state
print("\n=== Final state ===")
cur.execute("""
    SELECT d.id, d.title, d.cover,
           (SELECT COUNT(*) FROM "Episode" WHERE "dramaId" = d.id) as ep_count
    FROM "Drama" d 
    WHERE d.title ILIKE '%%jenderal%%'
    ORDER BY d.title
""")
for r in cur.fetchall():
    print(f"  {r[0]} | {r[1]} | eps={r[3]} | {r[2][:70]}")

cur.close()
conn.close()
print("\nDone!")
