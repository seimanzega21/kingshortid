import psycopg2, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

conn = psycopg2.connect('postgresql://postgres:seiman21@localhost:5432/kingshort')
cur = conn.cursor()

# Check dubbing dramas
cur.execute("""
    SELECT id, title, 
           CASE WHEN description IS NULL THEN 'NULL' 
                WHEN description = '' THEN 'EMPTY' 
                ELSE LEFT(description, 50) END as desc_preview,
           CASE WHEN cover IS NULL THEN 'NULL'
                WHEN cover = '' THEN 'EMPTY'
                ELSE LEFT(cover, 60) END as cover_preview,
           "totalEpisodes", "isActive", "createdAt",
           genres::text, "tagList"::text
    FROM "Drama" 
    WHERE description LIKE '%%Sulih Suara%%' 
       OR "tagList"::text LIKE '%%Dubbing%%'
    ORDER BY "createdAt" DESC
    LIMIT 10
""")

rows = cur.fetchall()
print(f"=== Dubbing Dramas ({len(rows)} shown) ===")
for r in rows:
    print(f"\n  ID:     {r[0]}")
    print(f"  Title:  {r[1][:50]}")
    print(f"  Desc:   {r[2]}")
    print(f"  Cover:  {r[3]}")
    print(f"  EpsCnt: {r[4]}")
    print(f"  Active: {r[5]}")
    print(f"  Date:   {r[6]}")
    print(f"  Genres: {r[7]}")
    print(f"  Tags:   {r[8]}")

# Check episodes for first drama
if rows:
    did = rows[0][0]
    cur.execute("""
        SELECT COUNT(*) FROM "Episode" WHERE "dramaId" = %s
    """, (did,))
    ep_count = cur.fetchone()[0]
    print(f"\n=== Episodes for '{rows[0][1][:30]}' ===")
    print(f"  Episode count: {ep_count}")
    
    if ep_count > 0:
        cur.execute("""
            SELECT "episodeNumber", title, LEFT("videoUrl", 60) as url, duration, "isActive"
            FROM "Episode" WHERE "dramaId" = %s
            ORDER BY "episodeNumber" LIMIT 5
        """, (did,))
        for ep in cur.fetchall():
            print(f"  Ep{ep[0]}: {ep[1][:30]} url={ep[2]} dur={ep[3]} active={ep[4]}")

# Also check total counts
cur.execute('SELECT COUNT(*) FROM "Drama"')
print(f"\nTotal dramas: {cur.fetchone()[0]}")
cur.execute('SELECT COUNT(*) FROM "Episode"')
print(f"Total episodes: {cur.fetchone()[0]}")

conn.close()
