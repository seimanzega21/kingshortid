import psycopg2

def search(url, name):
    try:
        conn = psycopg2.connect(url)
        cur = conn.cursor()
        cur.execute("SELECT id, title FROM \"dramas\" WHERE title ILIKE '%salah sangka%' OR title ILIKE '%jadi ayah%'")
        res = cur.fetchall()
        print(f"[{name}] dramas table:", res)
    except Exception as e:
        print(f"[{name}] dramas table error:", e)

    try:
        conn = psycopg2.connect(url)
        cur = conn.cursor()
        cur.execute("SELECT id, title FROM \"Drama\" WHERE title ILIKE '%salah sangka%' OR title ILIKE '%jadi ayah%'")
        res = cur.fetchall()
        print(f"[{name}] Drama table:", res)
    except Exception as e:
        pass

search('postgresql://postgres:seiman21@localhost:5432/kingshort', 'Local DB')
search('postgresql://supabase_admin:GoZViiH1AXLl73BqLdKDtpeGgwUzfW64@10.0.3.14:5432/postgres', 'Prod VPS DB')
