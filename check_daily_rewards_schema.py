import psycopg2

URL = "postgresql://postgres:GoZViiH1AXLl73BqLdKDtpeGgwUzfW64@localhost:5435/postgres"

def main():
    try:
        conn = psycopg2.connect(URL)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'daily_rewards'
        """)
        cols = cur.fetchall()
        print("Columns in VPS 'daily_rewards':")
        for col in cols:
            print(f"  {col[0]} ({col[1]}), Nullable: {col[2]}")
            
        cur.close()
        conn.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
