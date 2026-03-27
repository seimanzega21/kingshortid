import psycopg2, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
conn = psycopg2.connect('postgresql://postgres:seiman21@localhost:5432/kingshort')
cur = conn.cursor()

# List all tables
cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
tables = [r[0] for r in cur.fetchall()]
print('Tables:', tables)

# Check Drama/Series table
for t in tables:
    if 'drama' in t.lower() or 'video' in t.lower() or 'episode' in t.lower() or 'content' in t.lower() or 'series' in t.lower() or 'media' in t.lower():
        cur.execute(f'SELECT COUNT(*) FROM "{t}"')
        cnt = cur.fetchone()[0]
        print(f'  Table "{t}": {cnt} rows')
        # Show columns
        cur.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name='{t}' ORDER BY ordinal_position LIMIT 15")
        cols = [c[0] for c in cur.fetchall()]
        print(f'    Columns: {cols}')

conn.close()
