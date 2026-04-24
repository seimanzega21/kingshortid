import os
import psycopg2
from dotenv import load_dotenv

load_dotenv('d:/kingshortid/cf-backend/.env')

db_url = os.environ.get('DATABASE_URL')
if not db_url:
    supabase_url = os.environ.get('SUPABASE_URL', '')
    pwd = os.environ.get('SUPABASE_DB_PASSWORD', '')
    host = supabase_url.replace('https://', '').replace('http://', '').split(':')[0]
    db_url = f"postgresql://postgres:{pwd}@{host}:5432/postgres"

try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM episodes;")
    total = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM episodes WHERE video_url_540p IS NOT NULL;")
    with_540p = cur.fetchone()[0]
    
    print(f"Total episodes: {total}")
    print(f"Episodes with 540p: {with_540p}")
    
    # Let's get a few 540p URLs and non-540p URLs
    cur.execute("SELECT video_url, video_url_540p FROM episodes WHERE video_url_540p IS NOT NULL LIMIT 2;")
    print("Example with 540p:", cur.fetchall())
    
    cur.execute("SELECT video_url, video_url_540p FROM episodes WHERE video_url_540p IS NULL LIMIT 2;")
    print("Example without 540p:", cur.fetchall())
    
    conn.close()
except Exception as e:
    print(e)
