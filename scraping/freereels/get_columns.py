"""Get exact Drama table columns"""
import psycopg2, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
conn = psycopg2.connect('postgresql://postgres:seiman21@localhost:5432/kingshort')
cur = conn.cursor()
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'Drama' ORDER BY ordinal_position")
cols = [r[0] for r in cur.fetchall()]
print(f'Drama columns ({len(cols)}):')
for c in cols:
    print(f'  {c}')

# Also Episode columns
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'Episode' ORDER BY ordinal_position")
ecols = [r[0] for r in cur.fetchall()]
print(f'\nEpisode columns ({len(ecols)}):')
for c in ecols:
    print(f'  {c}')
conn.close()
