import psycopg2, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
c = psycopg2.connect('postgresql://postgres:seiman21@localhost:5432/kingshort')
cur = c.cursor()

# Search for any drama with partial ID
cur.execute("""SELECT id, title FROM "Drama" WHERE id LIKE '2cd7fa2e%%' """)
rows = cur.fetchall()
print(f'Dramas with id starting "2cd7fa2e": {len(rows)}')
for r in rows:
    print(f'  {r[0]} | {r[1]}')

# Search for Bertahan
cur.execute("""SELECT id, title, cover, "totalEpisodes" FROM "Drama" WHERE title LIKE '%%Bertahan%%' """)
rows2 = cur.fetchall()
print(f'\nDramas with "Bertahan" in title: {len(rows2)}')
for r in rows2:
    print(f'  {r[0]} | {r[1]} | cover={r[2][:40] if r[2] else "NONE"} | eps={r[3]}')

# Check admin API: what does the drama list endpoint return?
# Also check if there's a drizzle-style "dramas" table
cur.execute("""SELECT table_name FROM information_schema.tables 
               WHERE table_schema = 'public' AND table_name IN ('Drama', 'dramas', 'Episode', 'episodes')""")
print(f'\nRelevant tables:')
for t in cur.fetchall():
    print(f'  {t[0]}')

# Count dramas in both tables if they exist
for table in ['Drama', 'dramas']:
    try:
        cur.execute(f'SELECT COUNT(*) FROM "{table}"')
        print(f'  {table}: {cur.fetchone()[0]} rows')
    except Exception as e:
        c.rollback()
        print(f'  {table}: does not exist')

c.close()
