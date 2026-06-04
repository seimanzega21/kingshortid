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

def list_files(prefix):
    paginator = r2.get_paginator('list_objects_v2')
    files = []
    for page in paginator.paginate(Bucket=BUCKET, Prefix=prefix):
        for obj in page.get('Contents', []):
            files.append(obj['Key'])
    return files

def main():
    samples = [
        'netshortv2/perangkap-cinta-yang-salah/',
        'dramas/microdrama/dua-bayi-ajaib/'
    ]
    for sample in samples:
        files = list_files(sample)
        print(f"\n[*] Files in {sample} ({len(files)} files):")
        for f in sorted(files)[:15]:
            print(f"  - {f}")
        if len(files) > 15:
            print(f"  ... (+{len(files)-15} more)")

if __name__ == "__main__":
    main()
