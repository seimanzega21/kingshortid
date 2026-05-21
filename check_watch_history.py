import psycopg2

URL = "postgresql://postgres:GoZViiH1AXLl73BqLdKDtpeGgwUzfW64@localhost:5435/postgres"

def main():
    try:
        conn = psycopg2.connect(URL)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT user_id, drama_id, episode_id, COUNT(*)
            FROM watch_history
            GROUP BY user_id, drama_id, episode_id
            HAVING COUNT(*) > 1
        """)
        dups = cur.fetchall()
        print(f"Duplicate watch history entries: {len(dups)}")
        for d in dups[:10]:
            print(f"  User: {d[0]}, Drama: {d[1]}, Ep: {d[2]}, Count: {d[3]}")
            
        cur.close()
        conn.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
