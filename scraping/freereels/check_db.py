import psycopg2, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
conn = psycopg2.connect('postgresql://postgres:seiman21@localhost:5432/kingshort')
cur = conn.cursor()

# Check total episodes from FreeReels
cur.execute("SELECT COUNT(*), \"isActive\" FROM video WHERE source='freereels' GROUP BY \"isActive\"")
rows = cur.fetchall()
print('FreeReels episodes by isActive:')
for row in rows:
    print(f'  count={row[0]} isActive={row[1]}')

# Check if there are episodes at all
cur.execute("SELECT COUNT(*) FROM video WHERE source='freereels'")
total = cur.fetchone()[0]
print(f'Total freereels videos: {total}')

# Show recent ones
cur.execute("SELECT id, title, episode, \"isActive\", \"createdAt\" FROM video WHERE source='freereels' ORDER BY \"createdAt\" DESC LIMIT 5")
rows = cur.fetchall()
print('Latest freereels videos:')
for r in rows:
    print(f'  id={r[0]} title={str(r[1])[:40]} ep={r[2]} active={r[3]} created={r[4]}')

# Also check what columns exist in video table
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='video' ORDER BY ordinal_position")
cols = [c[0] for c in cur.fetchall()]
print(f'\nVideo table columns: {cols}')

conn.close()
