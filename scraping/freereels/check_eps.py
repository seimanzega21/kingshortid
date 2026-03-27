import psycopg2, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
conn = psycopg2.connect('postgresql://postgres:seiman21@localhost:5432/kingshort')
cur = conn.cursor()

# Check episodes per drama for dramas with FRkey
cur.execute("""
    SELECT d.title, d."totalEpisodes",
           COUNT(e.id) AS actual_ep_count,
           MIN(e."episodeNumber") AS min_ep,
           MAX(e."episodeNumber") AS max_ep
    FROM "Drama" d
    LEFT JOIN "Episode" e ON e."dramaId" = d.id
    WHERE d.description LIKE '%[FRkey:%'
    GROUP BY d.id, d.title, d."totalEpisodes"
    ORDER BY d.title
""")
rows = cur.fetchall()
print('Drama episodes breakdown:')
for r in rows:
    print(f'  {str(r[0])[:35]} | totalEp={r[1]} | actual={r[2]} | range=ep{r[3]}-ep{r[4]}')

# Total episodes in DB for freereels dramas
cur.execute("""
    SELECT COUNT(e.id)
    FROM "Episode" e
    JOIN "Drama" d ON e."dramaId" = d.id
    WHERE d.description LIKE '%[FRkey:%'
""")
total_eps = cur.fetchone()[0]
print(f'\nTotal episodes in DB for FreeReels dramas: {total_eps}')

# Show sample episode data
cur.execute("""
    SELECT e."episodeNumber", e."isActive", e."videoUrl", d.title
    FROM "Episode" e
    JOIN "Drama" d ON e."dramaId" = d.id
    WHERE d.description LIKE '%[FRkey:%'
    ORDER BY e."createdAt" DESC
    LIMIT 10
""")
rows = cur.fetchall()
print('\nLatest episodes in DB:')
for r in rows:
    print(f'  ep{r[0]} active={r[1]} url={str(r[2])[:50]} drama={str(r[3])[:30]}')

conn.close()
