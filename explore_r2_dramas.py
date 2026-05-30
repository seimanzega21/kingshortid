# -*- coding: utf-8 -*-
# Cek struktur folder dramas/ di R2 dan cari drama target

import sys
import boto3
import requests
import re
from botocore.config import Config

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
BUCKET      = 'shortlovers'
API_BASE    = 'https://api.shortlovers.id'

r2 = boto3.client(
    's3',
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_KEY_ID,
    aws_secret_access_key=R2_SECRET,
    config=Config(signature_version='s3v4'),
    region_name='auto'
)

TARGET_DRAMAS = [
    "Jangan Tangisi Kepergianku",
    "Tombak Sakti Gadis Desa",
    "Makhluk Abadi",
    "Pedang sakti Sang Menantu Desa",
    "Edukasi Seks Oleh Sahabatku",
    "Istri Magang Bosku",
    "Titisan Dewa Obat",
    "Warisan Mata Sakti",
]

def normalize(title):
    return re.sub(r'\s+', ' ', title.strip().lower())

# 1. List sub-prefixes di dramas/
print("=== SUB-FOLDER DI dramas/ ===")
resp = r2.list_objects_v2(Bucket=BUCKET, Delimiter='/', Prefix='dramas/')
for cp in resp.get('CommonPrefixes', [])[:20]:
    print(f"  {cp['Prefix']}")
print(f"  ... (total: {len(resp.get('CommonPrefixes', []))} prefixes)")

# 2. Cek sub-folder di converted/
print("\n=== SUB-FOLDER DI converted/ ===")
resp2 = r2.list_objects_v2(Bucket=BUCKET, Delimiter='/', Prefix='converted/')
for cp in resp2.get('CommonPrefixes', [])[:10]:
    print(f"  {cp['Prefix']}")
print(f"  ... (total: {len(resp2.get('CommonPrefixes', []))} prefixes)")

# 3. Fetch drama list dari API + cek drama_id vs r2_id mismatch
print("\n=== FETCH DRAMA API (cari field r2/storage/video_id) ===")
r = requests.get(f"{API_BASE}/api/dramas?limit=1000", timeout=30)
dramas = r.json()
if not isinstance(dramas, list):
    dramas = dramas.get('dramas', dramas.get('data', []))

# Cari sample drama dan print semua fieldnya
sample_titles = ["Jangan Tangisi Kepergianku", "Warisan Mata Sakti", "Istri Magang Bosku"]
for sample in sample_titles:
    norm = normalize(sample)
    for d in dramas:
        if normalize(d.get('title', '')) == norm:
            print(f"\n--- {d.get('title')} ---")
            for k, v in d.items():
                if not isinstance(v, (dict, list)):
                    print(f"  {k}: {v}")
            break

# 4. Cek apakah ada drama yang judulnya mengandung kata target di dramas/ prefix
print("\n=== CEK ID DRAMA DI API vs PREFIX R2 ===")
# Ambil semua sub-folder di dramas/ dulu
all_r2_dramas_prefixes = []
paginator = r2.get_paginator('list_objects_v2')
for page in paginator.paginate(Bucket=BUCKET, Delimiter='/', Prefix='dramas/'):
    for cp in page.get('CommonPrefixes', []):
        all_r2_dramas_prefixes.append(cp['Prefix'])

print(f"Total prefix di dramas/: {len(all_r2_dramas_prefixes)}")

# Cari drama target di API dan cek berbagai ID field
for title in TARGET_DRAMAS:
    norm = normalize(title)
    found = None
    for d in dramas:
        if normalize(d.get('title', '')) == norm:
            found = d
            break
        if norm in normalize(d.get('title', '')):
            found = d
    
    if found:
        api_id = found.get('id', '')
        # Cek semua ID-related field
        id_fields = {k: v for k, v in found.items() if 'id' in k.lower() and isinstance(v, str)}
        
        # Cek apakah ada di R2
        in_r2 = any(api_id in p for p in all_r2_dramas_prefixes)
        
        # Cek field lain yang mungkin jadi prefix R2
        for fk, fv in id_fields.items():
            if any(fv in p for p in all_r2_dramas_prefixes):
                print(f"[MATCH R2] {title} | field={fk} value={fv}")
        
        if not in_r2:
            print(f"[NO R2] {title} | api_id={api_id} | id_fields={id_fields}")
