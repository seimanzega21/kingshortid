import psycopg2

VPS = 'postgresql://supabase_admin:GoZViiH1AXLl73BqLdKDtpeGgwUzfW64@141.11.160.187:5432/postgres'
try:
    conn = psycopg2.connect(VPS)
    cur = conn.cursor()
    cur.execute('SELECT count(*) FROM episodes')
    print("Has episodes table")
    conn.close()
except psycopg2.Error as e:
    print(e.pgerror)
except Exception as e:
    print(e)
