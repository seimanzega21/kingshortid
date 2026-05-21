import psycopg2

URL = "postgresql://postgres:GoZViiH1AXLl73BqLdKDtpeGgwUzfW64@localhost:5435/postgres"

def check_table(cur, table_name):
    print(f"\n=== COLUMNS IN '{table_name}' ===")
    cur.execute(f"""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = '{table_name}'
        ORDER BY ordinal_position
    """)
    cols = cur.fetchall()
    for col in cols:
        print(f"  {col[0]} ({col[1]}), Nullable: {col[2]}, Default: {col[3]}")

def main():
    try:
        conn = psycopg2.connect(URL)
        cur = conn.cursor()
        
        check_table(cur, 'users')
        check_table(cur, 'dramas')
        check_table(cur, 'episodes')
        check_table(cur, 'app_settings')
        
        cur.close()
        conn.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
