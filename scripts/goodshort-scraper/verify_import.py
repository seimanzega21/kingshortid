import psycopg2

conn = psycopg2.connect('postgresql://postgres:seiman21@localhost:5432/kingshort')
cur = conn.cursor()

# Count total dramas
cur.execute('SELECT COUNT(*) FROM "Drama"')
total = cur.fetchone()[0]

# Count total episodes
cur.execute('SELECT COUNT(*) FROM "Episode"')
episodes = cur.fetchone()[0]

# Get most recent dramas (last 3)
cur.execute("""
    SELECT id, title, country, "totalEpisodes", "createdAt"::text, 
           LEFT(description, 80) as desc_preview
    FROM "Drama" 
    ORDER BY "createdAt" DESC 
    LIMIT 3
""")
rows = cur.fetchall()

print(f'\n=== DATABASE STATUS ===')
print(f'Total Dramas: {total}')
print(f'Total Episodes: {episodes}')

print(f'\n=== Last 3 Created Dramas ===\n')
for r in rows:
    print(f'Title: {r[1]}')
    print(f'Country: {r[2]} | Episodes: {r[3]} | Created: {r[4][:19]}')
    print(f'Description: {r[5]}...')
    print()

# Check if any drama has "Cinta" or "Hidup" in title
cur.execute("""
    SELECT id, title, country, "totalEpisodes"
    FROM "Drama" 
    WHERE title LIKE '%Cinta%' OR title LIKE '%Hidup%'
""")
goodshort_check = cur.fetchall()

print(f'=== Dramas matching "Cinta" or "Hidup" ===')
if goodshort_check:
    for g in goodshort_check:
        print(f'{g[1]} ({g[2]}) - {g[3]} episodes')
else:
    print('NONE FOUND!')

conn.close()
