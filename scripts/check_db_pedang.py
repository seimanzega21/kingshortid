import psycopg2
VPS = 'postgresql://supabase_admin:GoZViiH1AXLl73BqLdKDtpeGgwUzfW64@141.11.160.187:5432/postgres'
try:
    conn = psycopg2.connect(VPS)
    cur = conn.cursor()
    cur.execute("SELECT id, title FROM dramas WHERE title ILIKE '%Pedang%' OR title ILIKE '%Masakanku%' OR title ILIKE '%Robot%'")
    rows = cur.fetchall()
    print('FOUND IN DB:')
    for r in rows: print(r)
except Exception as e:
    print(e)
