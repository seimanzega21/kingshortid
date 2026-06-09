import psycopg2

DB_URL = "postgresql://postgres:GoZViiH1AXLl73BqLdKDtpeGgwUzfW64@141.11.160.187:5432/postgres"

def main():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT t.user_id, u.email, u.name, t.amount, t.description, t.reference, t.created_at, u.vip_status, u.vip_expiry, u.coins, u.purchased_coins
            FROM coin_transactions t
            JOIN users u ON t.user_id = u.id
            WHERE t.type = 'spend' AND t.reference LIKE 'ad_free_%'
            ORDER BY t.created_at DESC
            LIMIT 10;
        """)
        
        rows = cur.fetchall()
        print("=== RECENT VIP EXCHANGES (ALL USERS) ===")
        for r in rows:
            print(f"User: {r[2]} ({r[1]})")
            print(f"  Tx: {r[4]} | Ref: {r[5]} | Date: {r[6]}")
            print(f"  DB User State -> VIP: {r[7]} | Expiry: {r[8]} | Coins: {r[9]} + Purchased: {r[10]}")
            print("-" * 50)
            
        cur.close()
        conn.close()
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
