"""Check VPS dramas & episodes column names"""
import psycopg2, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

VPS = 'postgresql://supabase_admin:GoZViiH1AXLl73BqLdKDtpeGgwUzfW64@127.0.0.1:15432/postgres'
conn = psycopg2.connect(VPS)
cur = conn.cursor()

for t in ['dramas', 'episodes']:
    cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{t}' ORDER BY ordinal_position")
    cols = cur.fetchall()
    print(f'{t} ({len(cols)} columns):')
    for c in cols:
        print(f'  {c[0]}: {c[1]}')
    print()

# Count existing
cur.execute('SELECT COUNT(*) FROM dramas')
print(f'Existing dramas: {cur.fetchone()[0]}')
cur.execute('SELECT COUNT(*) FROM episodes')
print(f'Existing episodes: {cur.fetchone()[0]}')
conn.close()
