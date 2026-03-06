#!/usr/bin/env python3
"""Check R2 state and verify uploads"""
import boto3, os, sys, io
from dotenv import load_dotenv
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stdout.reconfigure(line_buffering=True)

load_dotenv(Path(__file__).parent / '.env')

s3 = boto3.client('s3',
    endpoint_url=os.getenv('R2_ENDPOINT'),
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
    region_name='auto'
)
bucket = os.getenv('R2_BUCKET_NAME', 'shortlovers')

# 1. List ALL top-level prefixes
print("=== TOP-LEVEL PREFIXES ===")
resp = s3.list_objects_v2(Bucket=bucket, Delimiter='/', MaxKeys=100)
for p in resp.get('CommonPrefixes', []):
    print(f"  {p['Prefix']}")
print(f"  Top-level files: {resp.get('KeyCount', 0)}")

# 2. Check melolo/ prefix specifically
print("\n=== MELOLO/ PREFIX ===")
resp = s3.list_objects_v2(Bucket=bucket, Prefix='melolo/', MaxKeys=50)
contents = resp.get('Contents', [])
print(f"Objects: {len(contents)}")
for obj in contents[:20]:
    print(f"  {obj['Size']:>10} {obj['Key']}")

# 3. Check if the test upload worked
print("\n=== TEST FILE CHECK ===")
try:
    resp = s3.head_object(Bucket=bucket, Key='melolo/_test.json')
    print(f"melolo/_test.json EXISTS ({resp['ContentLength']} bytes)")
except:
    print("melolo/_test.json NOT FOUND")

# 4. Check dewa-judi metadata
try:
    resp = s3.head_object(Bucket=bucket, Key='melolo/dewa-judi-era-90-an/metadata.json')
    print(f"dewa-judi metadata EXISTS ({resp['ContentLength']} bytes)")
except:
    print("dewa-judi metadata NOT FOUND")

# 5. Count how many drama-level folders exist under melolo/
print("\n=== MELOLO DRAMA FOLDERS ON R2 ===")
resp = s3.list_objects_v2(Bucket=bucket, Prefix='melolo/', Delimiter='/', MaxKeys=100)
drama_prefixes = resp.get('CommonPrefixes', [])
print(f"Drama folders: {len(drama_prefixes)}")
for p in drama_prefixes[:10]:
    print(f"  {p['Prefix']}")

print("\nDone!")
