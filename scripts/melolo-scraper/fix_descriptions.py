import psycopg2, os, json, boto3
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
load_dotenv(Path(__file__).parent.parent / 'backend' / '.env')

url = os.getenv('DATABASE_URL').split('?')[0]
conn = psycopg2.connect(url)
cur = conn.cursor()

s3 = boto3.client('s3',
    endpoint_url=os.getenv('R2_ENDPOINT'),
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
    region_name='auto'
)
BUCKET = 'shortlovers'

# Get all active dramas
cur.execute("""
    SELECT id, title, description, cover
    FROM "Drama"
    WHERE "isActive" = true
    ORDER BY title
""")
dramas = cur.fetchall()

print(f"Checking {len(dramas)} active dramas...\n")

fixed = 0
skipped = 0
no_meta = 0

for drama_id, title, desc, cover in dramas:
    # Extract slug from cover URL
    slug = None
    if cover and 'melolo/' in cover:
        parts = cover.split('melolo/')
        if len(parts) > 1:
            slug = parts[1].split('/')[0]
    
    if not slug:
        print(f"  ⚠️  {title}: No slug from cover")
        no_meta += 1
        continue
    
    # Get description from R2 metadata
    try:
        resp = s3.get_object(Bucket=BUCKET, Key=f'melolo/{slug}/metadata.json')
        meta = json.loads(resp['Body'].read().decode('utf-8'))
        r2_desc = meta.get('description', '').strip()
    except:
        no_meta += 1
        continue
    
    # Check if description needs fixing
    current_ok = desc and len(desc) > 20 and desc != title and 'Episode' not in desc
    has_r2_desc = r2_desc and len(r2_desc) > 20
    
    if current_ok:
        skipped += 1
        continue
    
    if has_r2_desc:
        cur.execute('UPDATE "Drama" SET description = %s WHERE id = %s', (r2_desc, drama_id))
        fixed += 1
        print(f"  ✅ {title}")
        print(f"     Old: {(desc or 'empty')[:60]}")
        print(f"     New: {r2_desc[:60]}")
    else:
        print(f"  ❌ {title}: No good description (DB: '{(desc or 'empty')[:40]}', R2: '{r2_desc[:40] if r2_desc else 'empty'}')")

conn.commit()

print(f"\n{'='*50}")
print(f"Fixed:    {fixed}")
print(f"Skipped:  {skipped} (already good)")
print(f"No meta:  {no_meta}")
print(f"Total:    {len(dramas)}")

cur.close()
conn.close()
