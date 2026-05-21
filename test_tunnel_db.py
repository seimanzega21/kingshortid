import psycopg2

URL = "postgresql://postgres:GoZViiH1AXLl73BqLdKDtpeGgwUzfW64@localhost:5435/postgres"

def main():
    try:
        print("Connecting to DB on localhost:5435...")
        conn = psycopg2.connect(URL)
        cur = conn.cursor()
        print("Connected successfully!")
        
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
        tables = [t[0] for t in cur.fetchall()]
        print("Tables list:", tables)
        
        cur.execute("SELECT COUNT(*) FROM users")
        print("Users count:", cur.fetchone()[0])
        
        cur.close()
        conn.close()
    except Exception as e:
        print("Error connecting to DB:", e)

if __name__ == "__main__":
    main()
