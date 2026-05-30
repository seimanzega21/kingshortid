# -*- coding: utf-8 -*-
# Cek struktur folder di R2 bucket untuk tahu format prefix yang dipakai

import sys
import boto3
from botocore.config import Config

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
BUCKET      = 'shortlovers'

r2 = boto3.client(
    's3',
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_KEY_ID,
    aws_secret_access_key=R2_SECRET,
    config=Config(signature_version='s3v4'),
    region_name='auto'
)

# List top-level "folders" (common prefixes)
print("=== TOP-LEVEL PREFIXES DI BUCKET shortlovers ===")
response = r2.list_objects_v2(Bucket=BUCKET, Delimiter='/', MaxKeys=50)

print("\n[Folders/Prefixes]:")
for cp in response.get('CommonPrefixes', []):
    print(f"  {cp['Prefix']}")

print("\n[Files di root]:")
for obj in response.get('Contents', []):
    size_mb = obj.get('Size', 0) / (1024*1024)
    print(f"  {obj['Key']} ({size_mb:.2f} MB)")

# Ambil 1 sample ID yang kita tahu ada
SAMPLE_ID = 'v8zkp55vraxr5vivucx7l6d3'  # Jangan Tangisi Kepergianku
print(f"\n=== SEARCH LANGSUNG UNTUK ID: {SAMPLE_ID} ===")
response2 = r2.list_objects_v2(Bucket=BUCKET, Prefix=SAMPLE_ID[:8], MaxKeys=20)
for obj in response2.get('Contents', []):
    print(f"  {obj['Key']}")

# Coba list beberapa folder level pertama untuk melihat format
print("\n=== SAMPLE 30 FILE PERTAMA DI BUCKET ===")
response3 = r2.list_objects_v2(Bucket=BUCKET, MaxKeys=30)
for obj in response3.get('Contents', []):
    size_mb = obj.get('Size', 0) / (1024*1024)
    print(f"  {obj['Key']} ({size_mb:.2f} MB)")
