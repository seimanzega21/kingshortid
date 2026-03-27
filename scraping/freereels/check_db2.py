import psycopg2, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
conn = psycopg2.connect('postgresql://postgres:seiman21@localhost:5432/kingshort')
cur = conn.cursor()

# Check Drama table for freereels
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='Drama' ORDER BY ordinal_position")
drama_cols = [c[0] for c in cur.fetchall()]
print('Drama columns:', drama_cols)

cur.execute('SELECT COUNT(*) FROM "Drama" WHERE source=\'freereels\'')
drama_count = cur.fetchone()[0]
print(f'Dramas from freereels: {drama_count}')

# Check Episode table
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='Episode' ORDER BY ordinal_position")
ep_cols = [c[0] for c in cur.fetchall()]
print('\nEpisode columns:', ep_cols)

cur.execute('SELECT COUNT(*) FROM "Episode"')
ep_total = cur.fetchone()[0]
print(f'Total episodes in DB: {ep_total}')

# Check if episodes have dramaId linked to freereels dramas
cur.execute("""
    SELECT COUNT(e.id), e."isActive"
    FROM "Episode" e
    JOIN "Drama" d ON e."dramaId" = d.id
    WHERE d.source = 'freereels'
    GROUP BY e."isActive"
""")
rows = cur.fetchall()
print('\nFreereels episodes by isActive:')
for r in rows:
    print(f'  count={r[0]} isActive={r[1]}')

# Show latest drama titles from freereels
cur.execute('SELECT id, title, "isActive", source, "createdAt" FROM "Drama" WHERE source=\'freereels\' ORDER BY "createdAt" DESC LIMIT 5')
rows = cur.fetchall()
print('\nLatest freereels dramas:')
for r in rows:
    print(f'  id={r[0]} title={str(r[1])[:35]} active={r[2]} source={r[3]}')

# Show latest episodes
cur.execute("""
    SELECT e.id, e."episodeNumber", e."isActive", e."videoUrl", d.title
    FROM "Episode" e
    JOIN "Drama" d ON e."dramaId" = d.id
    WHERE d.source = 'freereels'
    ORDER BY e.id DESC
    LIMIT 5
""")
rows = cur.fetchall()
print('\nLatest freereels episodes:')
for r in rows:
    print(f'  ep_id={r[0]} ep_num={r[1]} active={r[2]} url={str(r[3])[:40]} drama={str(r[4])[:30]}')

conn.close()
