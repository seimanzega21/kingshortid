"""Check VPS DB schema via tunnel"""
import psycopg2, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

VPS = 'postgresql://supabase_admin:GoZViiH1AXLl73BqLdKDtpeGgwUzfW64@127.0.0.1:15432/postgres'
conn = psycopg2.connect(VPS)
cur = conn.cursor()

# List all schemas
cur.execute("SELECT schema_name FROM information_schema.schemata")
print('Schemas:')
for r in cur.fetchall():
    print(f'  {r[0]}')

# List tables in all schemas
cur.execute("SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema NOT IN ('information_schema', 'pg_catalog') ORDER BY table_schema, table_name")
print('\nTables:')
for r in cur.fetchall():
    print(f'  {r[0]}.{r[1]}')

# Try with search_path
cur.execute("SHOW search_path")
print(f'\nSearch path: {cur.fetchone()[0]}')

conn.close()
