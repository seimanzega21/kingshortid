import psycopg2, os, json, boto3
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
load_dotenv(Path(__file__).parent.parent / 'backend' / '.env')

conn = psycopg2.connect(os.getenv('DATABASE_URL').split('?')[0])
cur = conn.cursor()

# Check current DB data
cur.execute("""SELECT id, title, description, cover FROM "Drama" WHERE title ILIKE '%Mata Kiri%'""")
for r in cur.fetchall():
    print(f"DB ID: {r[0]}")
    print(f"DB Title: {r[1]}")
    print(f"DB Desc: {r[2]}")
    print(f"DB Cover: {r[3]}")
    print()

# Also check the deactivated one
cur.execute("""SELECT id, title, description FROM "Drama" WHERE title ILIKE '%Mata Kiri%' AND "isActive" = false""")
rows = cur.fetchall()
if rows:
    print("DEACTIVATED:")
    for r in rows:
        print(f"  ID: {r[0]}, Title: {r[1]}, Desc: {r[2][:80] if r[2] else 'NONE'}")

# Check R2 metadata
s3 = boto3.client('s3',
    endpoint_url=os.getenv('R2_ENDPOINT'),
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
    region_name='auto'
)

try:
    resp = s3.get_object(Bucket='shortlovers', Key='melolo/mata-kiri-ajaibku/metadata.json')
    meta = json.loads(resp['Body'].read().decode('utf-8'))
    print(f"\nR2 Title: {meta.get('title')}")
    print(f"R2 Desc: {meta.get('description')}")
except Exception as e:
    print(f"\nR2 error: {e}")

cur.close()
conn.close()
