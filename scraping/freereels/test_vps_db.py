"""Try different VPS DB connection methods"""
import psycopg2, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

VPS_IP = '141.11.160.187'
configs = [
    # Standard postgres port
    f'postgresql://postgres:GoZViH1AXL73BqLdkDtpeGgwUzfW64@{VPS_IP}:5432/postgres',
    f'postgresql://supabase_admin:GoZViiH1AXLl73BqLdKDtpeGgwUzfW64@{VPS_IP}:5432/postgres',
    # Common Supabase pooler ports
    f'postgresql://postgres:GoZViH1AXL73BqLdkDtpeGgwUzfW64@{VPS_IP}:6543/postgres',
    f'postgresql://supabase_admin:GoZViiH1AXLl73BqLdKDtpeGgwUzfW64@{VPS_IP}:6543/postgres',
    # Try port 5433 (common alternative)
    f'postgresql://postgres:GoZViH1AXL73BqLdkDtpeGgwUzfW64@{VPS_IP}:5433/postgres',
    f'postgresql://supabase_admin:GoZViiH1AXLl73BqLdKDtpeGgwUzfW64@{VPS_IP}:5433/postgres',
]

for url in configs:
    port = url.split(':')[3].split('/')[0]
    user = url.split('//')[1].split(':')[0]
    try:
        conn = psycopg2.connect(url, connect_timeout=5)
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM "Drama"')
        count = cur.fetchone()[0]
        print(f'SUCCESS! {user}@{port} - {count} dramas')
        conn.close()
        break
    except Exception as e:
        err = str(e).strip()[:80]
        print(f'FAIL {user}@{port}: {err}')
