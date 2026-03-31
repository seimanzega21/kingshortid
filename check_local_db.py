import psycopg2
try:
    conn = psycopg2.connect('postgresql://postgres:seiman21@localhost:5432/kingshort')
    cur = conn.cursor()
    
    cur.execute('SELECT COUNT(*) FROM episodes WHERE is_active = true')
    total = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM episodes WHERE is_active = true AND video_url_540p IS NOT NULL')
    p540 = cur.fetchone()[0]
    
    cur.execute('SELECT COUNT(*) FROM episodes WHERE is_active = true AND video_url LIKE ''%%720p%%''')
    p720 = cur.fetchone()[0]
    
    print(f'TOTAL_ACTIVE: {total}')
    print(f'HAS_540P: {p540}')
    print(f'HAS_720P: {p720}')
    
    # Check how many don't have 540p
    cur.execute('SELECT drama_id, COUNT(*) FROM episodes WHERE is_active = true AND video_url_540p IS NULL GROUP BY drama_id LIMIT 5')
    missing = cur.fetchall()
    if missing:
        print('Dramas missing 540p for some episodes:', missing)
        
    conn.close()
except Exception as e:
    print(e)
