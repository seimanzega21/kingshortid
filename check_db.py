import psycopg2

VPS = 'postgresql://supabase_admin:GoZViiH1AXLl73BqLdKDtpeGgwUzfW64@141.11.160.187:5432/postgres'
try:
    conn = psycopg2.connect(VPS)
    cur = conn.cursor()
    
    cur.execute('SELECT COUNT(*) FROM episodes WHERE is_active = true')
    total = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM episodes WHERE is_active = true AND video_url_540p IS NOT NULL')
    p540 = cur.fetchone()[0]
    
    print(f'TOTAL_ACTIVE: {total}')
    print(f'HAS_540P: {p540}')
    
    conn.close()
except Exception as e:
    print(e)
