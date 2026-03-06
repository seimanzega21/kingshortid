#!/usr/bin/env python3
"""
Upload 5 vidrama covers to R2 and update the database.
Covers already downloaded to vidrama_covers/ directory.
"""
import json, os, sys, requests, boto3
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / '.env')

R2_ENDPOINT = os.getenv('R2_ENDPOINT')
R2_ACCESS_KEY_ID = os.getenv('R2_ACCESS_KEY_ID')
R2_SECRET_ACCESS_KEY = os.getenv('R2_SECRET_ACCESS_KEY')
R2_BUCKET = os.getenv('R2_BUCKET_NAME', 'shortlovers')
R2_PUBLIC = 'https://stream.shortlovers.id'
BACKEND_URL = 'http://localhost:3001/api'

s3 = boto3.client('s3', endpoint_url=R2_ENDPOINT,
                   aws_access_key_id=R2_ACCESS_KEY_ID,
                   aws_secret_access_key=R2_SECRET_ACCESS_KEY,
                   region_name='auto')

# Mapping: local file -> drama slug in R2
COVERS = {
    'setelah_bertapa__kutaklukkan_dunia.webp': {
        'slug': 'setelah-bertapa-kutaklukkan-dunia',
        'title': 'Setelah Bertapa, Kutaklukkan Dunia',
    },
    'siapa_yang_sedang_membicarakan_kaisar.webp': {
        'slug': 'siapa-yang-sedang-membicarakan-kaisar',
        'title': 'Siapa yang Sedang Membicarakan Kaisar',
    },
    'sistem_perubah_nasib.webp': {
        'slug': 'sistem-perubah-nasib',
        'title': 'Sistem Perubah Nasib',
    },
    'sistem_suami_sultan.webp': {
        'slug': 'sistem-suami-sultan',
        'title': 'Sistem Suami Sultan',
    },
    'tahun_1977_penuh_peluang.webp': {
        'slug': 'tahun-1977-penuh-peluang',
        'title': 'Tahun 1977 Penuh Peluang',
    },
}

covers_dir = Path('vidrama_covers')

print("=" * 60)
print("  UPLOAD VIDRAMA COVERS TO R2 + UPDATE DB")
print("=" * 60)

uploaded = 0
failed = 0

for filename, info in COVERS.items():
    filepath = covers_dir / filename
    slug = info['slug']
    title = info['title']
    
    print(f"\n[{uploaded+failed+1}/5] {title}")
    
    if not filepath.exists():
        print(f"  ❌ File not found: {filepath}")
        failed += 1
        continue
    
    size = filepath.stat().st_size
    print(f"  File: {filepath} ({size:,} bytes)")
    
    # Upload to R2 as poster.webp
    r2_key = f'melolo/{slug}/poster.webp'
    try:
        s3.upload_file(str(filepath), R2_BUCKET, r2_key,
                      ExtraArgs={'ContentType': 'image/webp'})
        cover_url = f'{R2_PUBLIC}/melolo/{slug}/poster.webp'
        print(f"  ✅ Uploaded: {r2_key}")
        print(f"  URL: {cover_url}")
    except Exception as e:
        print(f"  ❌ R2 upload failed: {e}")
        failed += 1
        continue
    
    # Also upload as cover.webp for compatibility
    r2_key2 = f'melolo/{slug}/cover.webp'
    try:
        s3.upload_file(str(filepath), R2_BUCKET, r2_key2,
                      ExtraArgs={'ContentType': 'image/webp'})
        print(f"  ✅ Also uploaded: {r2_key2}")
    except:
        pass
    
    # Verify upload
    try:
        r = requests.head(cover_url, timeout=10)
        if r.status_code == 200:
            print(f"  ✅ Verified on CDN ({r.headers.get('content-length', '?')} bytes)")
        else:
            print(f"  ⚠️ CDN check: {r.status_code}")
    except:
        pass
    
    # Update database via backend API
    try:
        # Find drama by slug/title in database
        r = requests.get(f"{BACKEND_URL}/dramas?limit=200", timeout=10)
        if r.status_code == 200:
            dramas = r.json().get('dramas', [])
            drama = None
            for d in dramas:
                if d.get('slug') == slug or d.get('title') == title:
                    drama = d
                    break
            
            if drama:
                drama_id = drama['id']
                # Update cover_url
                update_r = requests.put(f"{BACKEND_URL}/dramas/{drama_id}", 
                    json={'coverUrl': cover_url},
                    timeout=10)
                if update_r.status_code == 200:
                    print(f"  ✅ Database updated (drama ID: {drama_id})")
                else:
                    print(f"  ⚠️ DB update failed: {update_r.status_code} - {update_r.text[:100]}")
            else:
                print(f"  ⚠️ Drama not found in database by slug '{slug}' or title '{title}'")
        else:
            print(f"  ⚠️ Failed to fetch dramas: {r.status_code}")
    except Exception as e:
        print(f"  ⚠️ DB update error: {e}")
    
    uploaded += 1

print(f"\n{'=' * 60}")
print(f"  DONE: {uploaded} uploaded, {failed} failed")
print(f"{'=' * 60}")
