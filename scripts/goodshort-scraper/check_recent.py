import psycopg2

conn = psycopg2.connect('postgresql://postgres:seiman21@localhost:5432/kingshort')
cur = conn.cursor()

# Check all dramas sorted by created date
cur.execute("""
    SELECT id, title, country, "totalEpisodes", "createdAt"::text 
    FROM "Drama" 
    ORDER BY "createdAt" DESC 
    LIMIT 5
""")
rows = cur.fetchall()

print(f'\n=== Last 5 Created Dramas ===\n')
for r in rows:
    print(f'{r[1][:50]:50} | {r[2]:12} | {r[3]:3} eps | {r[4][:19]}')

# Check episodes for Indonesian dramas
cur.execute("""
    SELECT d.title, COUNT(e.id) as episode_count
    FROM "Drama" d
    LEFT JOIN "Episode" e ON d.id = e."dramaId"
    WHERE d.country = 'Indonesia'
    GROUP BY d.id, d.title
    ORDER BY d."createdAt" DESC
    LIMIT 5
""")
rows = cur.fetchall()

print(f'\n=== Indonesian Dramas with Episode Count ===\n')
for r in rows:
    print(f'{r[0][:50]:50} | {r[1]:3} episodes')

conn.close()
