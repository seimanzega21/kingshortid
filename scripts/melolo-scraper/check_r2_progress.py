#!/usr/bin/env python3
"""Quick check: how many dramas on R2 vs local"""
import boto3, os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client('s3',
    endpoint_url=os.getenv('R2_ENDPOINT'),
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
    region_name='auto'
)

# Get dramas on R2
print("Checking R2...", flush=True)
r2_dramas = set()
paginator = s3.get_paginator('list_objects_v2')
for page in paginator.paginate(Bucket='shortlovers', Prefix='melolo/', Delimiter='/'):
    for prefix in page.get('CommonPrefixes', []):
        drama_slug = prefix['Prefix'].split('/')[1]
        if drama_slug:
            r2_dramas.add(drama_slug)

# Get local dramas
melolo_dir = Path('r2_ready/melolo')
local_dramas = {d.name for d in melolo_dir.iterdir() if d.is_dir()}

# Compare
print(f"\n✅ R2: {len(r2_dramas)} dramas")
print(f"📁 Local: {len(local_dramas)} dramas")
print(f"⏳ Pending: {len(local_dramas - r2_dramas)} dramas\n")

if len(local_dramas - r2_dramas) > 0:
    print("Pending dramas:")
    for slug in sorted(local_dramas - r2_dramas)[:10]:
        print(f"  - {slug}")
    if len(local_dramas - r2_dramas) > 10:
        print(f"  ... and {len(local_dramas - r2_dramas) - 10} more")
