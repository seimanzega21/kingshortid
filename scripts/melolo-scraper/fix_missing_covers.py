#!/usr/bin/env python3
"""
Step 1: Find covers for 8 dramas that are complete on R2 but missing covers.
Uses vidrama.asia og:image approach (same as the successful 5-cover fix).

Step 2: Upload covers to R2.
"""
import os, json, re, requests, boto3
from pathlib import Path
from dotenv import load_dotenv
from botocore.config import Config

load_dotenv(Path(__file__).parent / '.env')

config = Config(retries={'max_attempts': 3}, connect_timeout=10, read_timeout=30)
s3 = boto3.client('s3',
    endpoint_url=os.getenv('R2_ENDPOINT'),
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
    region_name='auto', config=config)
BUCKET = os.getenv('R2_BUCKET_NAME', 'shortlovers')
R2_PUBLIC = 'https://stream.shortlovers.id'
HEADERS = {"User-Agent": "Mozilla/5.0 Chrome/120.0.0.0"}
base = 'r2_ready/melolo'

# 8 dramas with complete episodes but NO cover on R2 (from audit)
NO_COVER_DRAMAS = [
    'balas-budi-jadi-cinta',
    'bangkit-dari-neraka',
    'bisnis-kaya-bareng-hewan',
    'cinta-sang-komandan',
    'guci-ajaib-di-hari-kiamat',
    'istri-desa-si-kapten',
    'istri-kesayangan-galak',
]

# Also check: some titles in audit show description instead of title
# "Rivan terlahir kembali..." is probably a drama with bad title in metadata
# Let's find ALL non-DB dramas without cover

print("="*70)
print("  FIXING MISSING COVERS FOR COMPLETE DRAMAS")
print("="*70)

# Get DB titles
r = requests.get('http://localhost:3001/api/dramas?limit=300', timeout=10)
db_titles = set(d.get('title','') for d in r.json().get('dramas', []))

# Find all non-DB dramas without R2 cover
missing_cover = []
for dirname in sorted(os.listdir(base)):
    dpath = os.path.join(base, dirname)
    if not os.path.isdir(dpath): continue
    meta_path = os.path.join(dpath, 'metadata.json')
    if not os.path.exists(meta_path): continue
    
    with open(meta_path, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    
    title = meta.get('title', dirname)
    if title in db_titles: continue
    
    # Check R2 for cover
    has_cover = False
    for cover_name in ['poster.webp', 'poster.jpg', 'cover.jpg', 'cover.webp', 'cover.png']:
        try:
            s3.head_object(Bucket=BUCKET, Key=f'melolo/{dirname}/{cover_name}')
            has_cover = True
            break
        except:
            pass
    
    if not has_cover:
        series_id = meta.get('series_id', '')
        slug = meta.get('slug', dirname)
        missing_cover.append({
            'dirname': dirname,
            'title': title,
            'slug': slug,
            'series_id': series_id,
            'total_eps': meta.get('total_episodes', 0),
        })

print(f"\nFound {len(missing_cover)} dramas without cover on R2:\n")
for d in missing_cover:
    print(f"  {d['dirname']}: {d['title'][:50]} (series_id: {d['series_id'][:20]})")

# Step 1: Try vidrama.asia og:image for each
print(f"\n{'='*70}")
print(f"  FETCHING COVERS FROM VIDRAMA.ASIA")
print(f"{'='*70}\n")

found_covers = {}
os.makedirs("vidrama_covers", exist_ok=True)

for d in missing_cover:
    slug = d['slug']
    sid = d['series_id']
    title = d['title']
    
    if sid:
        url = f"https://vidrama.asia/movie/{slug}--{sid}?provider=melolo"
    else:
        url = f"https://vidrama.asia/movie/{slug}?provider=melolo"
    
    print(f"  Fetching: {title[:50]}")
    print(f"    URL: {url}")
    
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code == 200:
            og = re.search(r'property="og:image"\s+content="([^"]+)"', r.text)
            if og:
                cover_url = og.group(1).replace('&amp;', '&')
                if cover_url != "https://vidrama.asia/og-image.jpg":
                    found_covers[d['dirname']] = cover_url
                    print(f"    ✅ Cover found!")
                else:
                    print(f"    ⚠️ Generic og-image (drama not found on vidrama)")
            else:
                print(f"    ❌ No og:image")
        else:
            print(f"    ❌ HTTP {r.status_code}")
    except Exception as e:
        print(f"    ❌ Error: {str(e)[:50]}")

print(f"\n  Found covers: {len(found_covers)}/{len(missing_cover)}")

# Step 2: Download and upload to R2
print(f"\n{'='*70}")
print(f"  DOWNLOADING AND UPLOADING COVERS")
print(f"{'='*70}\n")

uploaded = 0
for dirname, cover_url in found_covers.items():
    print(f"  {dirname}:")
    try:
        # Download
        r = requests.get(cover_url, headers=HEADERS, timeout=15)
        if r.status_code != 200 or len(r.content) < 1000:
            print(f"    ❌ Download failed ({r.status_code}, {len(r.content)} bytes)")
            continue
        
        ct = r.headers.get('content-type', 'image/webp')
        ext = 'webp' if 'webp' in ct else 'jpg' if 'jpeg' in ct else 'png' if 'png' in ct else 'webp'
        
        # Save locally
        local_path = f"vidrama_covers/{dirname}.{ext}"
        with open(local_path, 'wb') as f:
            f.write(r.content)
        
        # Upload to R2
        r2_key = f'melolo/{dirname}/poster.{ext}'
        s3.upload_file(local_path, BUCKET, r2_key,
                      ExtraArgs={'ContentType': f'image/{ext}'})
        
        # Also upload as cover.{ext}
        r2_key2 = f'melolo/{dirname}/cover.{ext}'
        s3.upload_file(local_path, BUCKET, r2_key2,
                      ExtraArgs={'ContentType': f'image/{ext}'})
        
        print(f"    ✅ Uploaded: poster.{ext} + cover.{ext} ({len(r.content):,} bytes)")
        uploaded += 1
    except Exception as e:
        print(f"    ❌ Error: {str(e)[:60]}")

# For dramas not found on vidrama, try generating a placeholder or using Melolo API
not_found = [d for d in missing_cover if d['dirname'] not in found_covers]
if not_found:
    print(f"\n  ⚠️ {len(not_found)} dramas still without cover:")
    for d in not_found:
        print(f"    - {d['title'][:55]}")

print(f"\n{'='*70}")
print(f"  DONE: {uploaded} covers uploaded to R2")
print(f"{'='*70}")
