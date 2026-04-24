import os
import psycopg2
from dotenv import load_dotenv

load_dotenv('d:/kingshortid/admin/.env')
clean_url = os.environ.get("DATABASE_URL").split("?")[0]
conn = psycopg2.connect(clean_url)
cur = conn.cursor()
cur.execute("SELECT table_schema, table_name FROM information_schema.tables WHERE table_type = 'BASE TABLE';")
for row in cur.fetchall():
    if row[0] not in ('information_schema', 'pg_catalog'):
        print(f"{row[0]}.{row[1]}")
cur.close()
conn.close()
