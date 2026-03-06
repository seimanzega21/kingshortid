"""Fix all remaining generic 'Drama pendek:' descriptions by finding better text from R2 metadata or deactivated duplicates"""
import psycopg2, os, json, boto3
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
load_dotenv(Path(__file__).parent.parent / 'backend' / '.env')

conn = psycopg2.connect(os.getenv('DATABASE_URL').split('?')[0])
cur = conn.cursor()

s3 = boto3.client('s3',
    endpoint_url=os.getenv('R2_ENDPOINT'),
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
    region_name='auto'
)

# Find all dramas with bad descriptions
cur.execute("""
    SELECT id, title, description, cover FROM "Drama"
    WHERE "isActive" = true
    AND (description LIKE 'Drama pendek:%' OR description IS NULL OR LENGTH(description) < 20)
    ORDER BY title
""")
bad = cur.fetchall()
print(f"Found {len(bad)} dramas with bad descriptions:\n")

for drama_id, title, desc, cover in bad:
    print(f"\n{'='*50}")
    print(f"{title}")
    print(f"  Current: '{desc}'")
    
    # Extract slug from cover
    slug = None
    if cover and 'melolo/' in cover:
        slug = cover.split('melolo/')[1].split('/')[0]
    
    # Try 1: Check deactivated duplicates (same cover)
    cur.execute("""SELECT title, description FROM "Drama" WHERE cover = %s AND "isActive" = false""", (cover,))
    deactivated = cur.fetchall()
    
    new_desc = None
    for d_title, d_desc in deactivated:
        # If deactivated description is better
        if d_desc and len(d_desc) > 30 and 'Drama pendek' not in d_desc:
            new_desc = d_desc
            print(f"  → From deactivated desc: {new_desc[:60]}")
            break
        # If deactivated TITLE is descriptive (contains sentence-like content)
        if len(d_title) > 30:
            new_desc = d_title
            print(f"  → From deactivated title: {new_desc[:60]}")
            break
    
    # Try 2: R2 metadata
    if not new_desc and slug:
        try:
            resp = s3.get_object(Bucket='shortlovers', Key=f'melolo/{slug}/metadata.json')
            meta = json.loads(resp['Body'].read().decode('utf-8'))
            r2_desc = meta.get('description', '').strip()
            if r2_desc and len(r2_desc) > 30 and 'Drama pendek' not in r2_desc:
                new_desc = r2_desc
                print(f"  → From R2 metadata: {new_desc[:60]}")
        except:
            pass
    
    if new_desc:
        cur.execute('UPDATE "Drama" SET description = %s WHERE id = %s', (new_desc, drama_id))
        conn.commit()
        print(f"  ✅ FIXED!")
    else:
        print(f"  ❌ No better description found")

# Final verification
cur.execute("""
    SELECT title, description FROM "Drama"
    WHERE "isActive" = true
    AND (description LIKE 'Drama pendek:%' OR description IS NULL OR LENGTH(description) < 20)
""")
remaining = cur.fetchall()
print(f"\n\nRemaining bad descriptions: {len(remaining)}")
for r in remaining:
    print(f"  {r[0]}: '{r[1]}'")

cur.close()
conn.close()
print("\nDone!")
