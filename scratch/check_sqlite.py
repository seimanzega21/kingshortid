import sqlite3

def check():
    db_path = "scripts/melolo-scraper/scraped_dramas.db"
    print(f"Connecting to SQLite: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # List tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables:", tables)
    
    # Try searching for Mendengar in all text columns
    for table_name_tup in tables:
        table_name = table_name_tup[0]
        try:
            cursor.execute(f"PRAGMA table_info({table_name});")
            cols = [c[1] for c in cursor.fetchall()]
            
            # Find rows
            for col in cols:
                cursor.execute(f"SELECT * FROM {table_name} WHERE {col} LIKE '%Mendengar%';")
                rows = cursor.fetchall()
                if rows:
                    print(f"Found match in {table_name}.{col}:")
                    for r in rows:
                        print("  ", r)
        except Exception as e:
            print(f"Error checking {table_name}: {e}")
            
    conn.close()

if __name__ == "__main__":
    check()
