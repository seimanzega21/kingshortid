import psycopg2
LOCAL_DB = 'postgresql://postgres:seiman21@localhost:5432/kingshort'
try:
    conn = psycopg2.connect(LOCAL_DB)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM \"Drama\" WHERE provider = 'idrama'")
    dramas = cur.fetchone()[0]
    print(f'iDrama Dramas: {dramas}')
    cur.execute("SELECT COUNT(*) FROM \"Episode\" e JOIN \"Drama\" d ON e.\"dramaId\" = d.id WHERE d.provider = 'idrama'")
    episodes = cur.fetchone()[0]
    print(f'iDrama Episodes: {episodes}')
    conn.close()
except Exception as e:
    print(e)
