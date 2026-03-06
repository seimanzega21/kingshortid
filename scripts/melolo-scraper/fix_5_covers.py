"""Download covers found in HARs and use HAR session to search remaining via API.
For dramas not in HARs, try direct cover URL patterns from other dramas' cover URLs."""
import json, os, re, requests, boto3
from dotenv import load_dotenv
from pathlib import Path
import psycopg2

load_dotenv()
load_dotenv(Path(__file__).parent.parent / 'backend' / '.env')

s3 = boto3.client('s3',
    endpoint_url=os.getenv('R2_ENDPOINT'),
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
    region_name='auto'
)
BUCKET = 'shortlovers'
R2_URL = 'https://stream.shortlovers.id'

url = os.getenv('DATABASE_URL').split('?')[0]
conn = psycopg2.connect(url)
cur = conn.cursor()

# Step 1: Scan ALL cover URLs from dramas that DO have real covers on R2
# to understand the CDN pattern
print("Step 1: Finding cover URL patterns from existing R2 metadata...\n")

existing_covers = {}
paginator = s3.get_paginator('list_objects_v2')
count = 0
for page in paginator.paginate(Bucket=BUCKET, Prefix='melolo/', Delimiter='/'):
    for prefix in page.get('CommonPrefixes', []):
        slug = prefix['Prefix'].replace('melolo/', '').rstrip('/')
        try:
            resp = s3.get_object(Bucket=BUCKET, Key=f'melolo/{slug}/metadata.json')
            meta = json.loads(resp['Body'].read().decode('utf-8'))
            cv = meta.get('cover_url', '')
            if cv and 'fizzopic' in cv:
                existing_covers[slug] = cv
                count += 1
                if count <= 3:
                    print(f"  {slug}: {cv[:100]}")
        except:
            pass
        if count >= 5:
            break  # We just need a sample
    if count >= 5:
        break

# Step 2: From existing cover URLs, extract the CDN pattern
# Cover URLs look like: https://p16-novel-sign-sg.fizzopic.org/novel-images-sg/{hash}~tplv-{params}
# The hash is unique per novel, but maybe we can derive it from the novel_id

# Step 3: Check each target - download from HAR findings or try scraped cover_url from metadata
print(f"\nStep 2: Checking targets...\n")

targets = {
    'setelah-bertapa-kutaklukkan-dunia': 'Setelah Bertapa, Kutaklukkan Dunia',
    'siapa-yang-sedang-membicarakan-kaisar': 'Siapa yang Sedang Membicarakan Kaisar',
    'sistem-perubah-nasib': 'Sistem Perubah Nasib',
    'sistem-suami-sultan': 'Sistem Suami Sultan',
    'tahun-1977-penuh-peluang': 'Tahun 1977 Penuh Peluang',
}

# Load HAR-found covers
har_covers = json.load(open('found_covers.json'))

for slug, title in targets.items():
    print(f"\n{'='*50}")
    print(f"{title}")
    
    # Try HAR-found cover first
    if slug in har_covers:
        cover_url = har_covers[slug]
        print(f"  HAR cover: {cover_url[:80]}")
        try:
            r = requests.get(cover_url, timeout=10)
            if r.status_code == 200 and len(r.content) > 1000:
                r2_key = f'melolo/{slug}/cover.jpg'
                s3.put_object(Bucket=BUCKET, Key=r2_key, Body=r.content, ContentType='image/jpeg')
                final_url = f'{R2_URL}/{r2_key}'
                cur.execute('UPDATE "Drama" SET cover = %s WHERE title = %s', (final_url, title))
                conn.commit()
                print(f"  ✅ Downloaded from HAR cover URL ({len(r.content)} bytes)")
                continue
            else:
                print(f"  ❌ HAR cover expired: {r.status_code}")
        except Exception as e:
            print(f"  ❌ HAR cover error: {e}")
    
    # Try existing metadata cover_url
    try:
        resp = s3.get_object(Bucket=BUCKET, Key=f'melolo/{slug}/metadata.json')
        meta = json.loads(resp['Body'].read().decode('utf-8'))
        cv = meta.get('cover_url', '')
        if cv and cv.startswith('http'):
            print(f"  Metadata cover: {cv[:80]}")
            try:
                r = requests.get(cv, timeout=10)
                if r.status_code == 200 and len(r.content) > 1000:
                    r2_key = f'melolo/{slug}/cover.jpg'
                    s3.put_object(Bucket=BUCKET, Key=r2_key, Body=r.content, ContentType='image/jpeg')
                    final_url = f'{R2_URL}/{r2_key}'
                    cur.execute('UPDATE "Drama" SET cover = %s WHERE title = %s', (final_url, title))
                    conn.commit()
                    print(f"  ✅ Downloaded from metadata cover_url ({len(r.content)} bytes)")
                    continue
                else:
                    print(f"  ❌ Metadata cover expired: {r.status_code}")
            except:
                print(f"  ❌ Metadata cover failed")
    except:
        pass
    
    # Last resort: Check if there's a cover file already on R2 (maybe uploaded via the ffmpeg approach)
    for name in ['cover.jpg', 'cover.png', 'cover.webp', 'poster.jpg']:
        try:
            s3.head_object(Bucket=BUCKET, Key=f'melolo/{slug}/{name}')
            final_url = f'{R2_URL}/melolo/{slug}/{name}'
            cur.execute('UPDATE "Drama" SET cover = %s WHERE title = %s', (final_url, title))
            conn.commit()
            print(f"  ✅ Using existing R2 cover: {name}")
            break
        except:
            pass
    else:
        print(f"  ❌ No cover available - needs manual scraping from Melolo app")

cur.close()
conn.close()
print("\nDone!")
