import psycopg2, os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
load_dotenv(Path(__file__).parent.parent / 'backend' / '.env')

url = os.getenv('DATABASE_URL').split('?')[0]
conn = psycopg2.connect(url)
cur = conn.cursor()

# Find dramas with the same cover URL (same content, different title)
print("=== DRAMAS WITH DUPLICATE COVERS ===\n")
cur.execute("""
    SELECT cover, COUNT(*) as cnt
    FROM "Drama"
    WHERE "isActive" = true AND cover IS NOT NULL AND cover != ''
    GROUP BY cover
    HAVING COUNT(*) > 1
    ORDER BY cnt DESC
""")
dupes = cur.fetchall()

total_dupes = 0
for cover, cnt in dupes:
    cur.execute("""
        SELECT id, title, "totalEpisodes", cover,
               (SELECT COUNT(*) FROM "Episode" WHERE "dramaId" = d.id) as real_eps,
               d."createdAt"
        FROM "Drama" d
        WHERE cover = %s AND "isActive" = true
        ORDER BY "createdAt"
    """, (cover,))
    rows = cur.fetchall()
    
    print(f"\n{'='*60}")
    print(f"Cover: {cover[:80]}...")
    print(f"Count: {cnt}")
    for r in rows:
        print(f"  [{r[0][:20]}...] {r[1]}")
        print(f"    Total: {r[2]}, Real eps: {r[4]}, Created: {r[5]}")
    total_dupes += cnt - 1  # extras

# Also check specifically mentioned ones
print(f"\n\n{'='*60}")
print("=== SPECIFIC CHECKS ===\n")

for keyword in ['Yusri', 'Kehadiran Cinta', 'Mata Kiri']:
    cur.execute("""
        SELECT id, title, cover, "totalEpisodes",
               (SELECT COUNT(*) FROM "Episode" WHERE "dramaId" = d.id) as real_eps
        FROM "Drama" d
        WHERE title ILIKE %s AND "isActive" = true
    """, (f'%{keyword}%',))
    rows = cur.fetchall()
    if rows:
        print(f"\n'{keyword}':")
        for r in rows:
            print(f"  [{r[0][:20]}...] {r[1]} | eps={r[4]} | cover={str(r[2])[:60]}")

print(f"\n\nTotal duplicate covers found: {total_dupes}")
cur.close()
conn.close()
