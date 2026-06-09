import psycopg2
import sys

# Direct DB connection using production password
DB_URL = "postgresql://postgres:GoZViiH1AXLl73BqLdKDtpeGgwUzfW64@141.11.160.187:5432/postgres"

def main():
    email = "ildafrika5@gmail.com"
    print(f"Querying user record for: {email}")
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        # Select user details
        cur.execute("""
            SELECT id, email, name, coins, purchased_coins, vip_status, vip_expiry, ad_free_expiry, updated_at
            FROM users
            WHERE email = %s;
        """, (email,))
        
        user = cur.fetchone()
        if not user:
            print(f"User {email} not found in database!")
            return
            
        columns = [desc[0] for desc in cur.description]
        user_dict = dict(zip(columns, user))
        
        print("\n=== USER DATABASE RECORD ===")
        for k, v in user_dict.items():
            print(f"{k}: {v} (Type: {type(v).__name__})")
            
        # Also let's check recent transactions
        print("\n=== RECENT COIN TRANSACTIONS ===")
        cur.execute("""
            SELECT id, type, amount, description, reference, created_at
            FROM coin_transactions
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 5;
        """, (user_dict['id'],))
        
        txs = cur.fetchall()
        for tx in txs:
            print(tx)
            
        cur.close()
        conn.close()
    except Exception as e:
        print("Error connecting/querying DB:", e)

if __name__ == "__main__":
    main()
