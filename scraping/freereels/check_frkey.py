import psycopg2, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
conn = psycopg2.connect('postgresql://postgres:seiman21@localhost:5432/kingshort')
cur = conn.cursor()

# Check which dramas have FRkey in description
cur.execute("SELECT id, title, description FROM \"Drama\" WHERE description LIKE '%[FRkey:%]%' LIMIT 20")
rows = cur.fetchall()
print(f'Dramas with [FRkey:] marker: {len(rows)}')
for r in rows:
    desc_end = r[2][-80:] if r[2] else ''
    print(f'  title={str(r[1])[:40]} desc_end={desc_end}')

# Also check total dramas vs episodes
cur.execute('SELECT COUNT(*) FROM "Drama"')
print(f'\nTotal dramas: {cur.fetchone()[0]}')
cur.execute('SELECT COUNT(*) FROM "Episode"')
print(f'Total episodes: {cur.fetchone()[0]}')

# Most recent dramas
cur.execute('SELECT id, title, "createdAt", "totalEpisodes" FROM "Drama" ORDER BY "createdAt" DESC LIMIT 10')
rows = cur.fetchall()
print('\nMost recent dramas:')
for r in rows:
    print(f'  {str(r[1])[:40]} eps={r[3]} created={r[2]}')

conn.close()
