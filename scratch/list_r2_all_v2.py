# -*- coding: utf-8 -*-
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

def main():
    paginator = r2.get_paginator('list_objects_v2')
    roots = ['freereels/', 'goodshort/', 'melolo/', 'microdrama/', 'netshortv2/']
    
    for root in roots:
        print(f"\n[*] Fetching prefixes in {root}...")
        prefixes = []
        for page in paginator.paginate(Bucket=BUCKET, Delimiter='/', Prefix=root):
            for cp in page.get('CommonPrefixes', []):
                prefixes.append(cp['Prefix'])
        print(f"Total prefixes in {root}: {len(prefixes)}")
        for p in sorted(prefixes)[:50]:
            print(f"  - {p}")
        if len(prefixes) > 50:
            print(f"  ... (+{len(prefixes)-50} more)")

if __name__ == "__main__":
    main()
