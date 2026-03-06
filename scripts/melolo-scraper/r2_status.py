#!/usr/bin/env python3
"""Quick R2 progress check for Vidrama scraping"""
import boto3, os
from dotenv import load_dotenv
load_dotenv()

s3 = boto3.client('s3',
    endpoint_url=os.getenv('R2_ENDPOINT'),
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'))
bucket = os.getenv('R2_BUCKET_NAME')

slugs = {}
total_files = 0
total_bytes = 0
paginator = s3.get_paginator('list_objects_v2')

for page in paginator.paginate(Bucket=bucket, Prefix='melolo/'):
    for obj in page.get('Contents', []):
        total_files += 1
        total_bytes += obj['Size']
        parts = obj['Key'].split('/')
        if len(parts) >= 2:
            sl = parts[1]
            if sl not in slugs:
                slugs[sl] = {'eps': 0, 'cover': False, 'meta': False}
            if obj['Key'].endswith('.mp4'):
                slugs[sl]['eps'] += 1
            elif 'cover' in obj['Key']:
                slugs[sl]['cover'] = True
            elif 'metadata' in obj['Key']:
                slugs[sl]['meta'] = True

complete = sum(1 for s in slugs.values() if s['eps'] > 0 and s['cover'])
total_eps = sum(s['eps'] for s in slugs.values())

print("=" * 50)
print("  R2 PROGRESS (melolo/)")
print("=" * 50)
print(f"  Drama folders:        {len(slugs)}")
print(f"  With video+cover:     {complete}")
print(f"  Total episode files:  {total_eps}")
print(f"  Total files:          {total_files}")
print(f"  Total size:           {total_bytes/1024/1024/1024:.2f} GB")
print()

# Avg episodes per drama
if complete > 0:
    avg = total_eps / len(slugs)
    print(f"  Avg eps/drama:        {avg:.1f}")

# Sample dramas
print()
print("--- Sample dramas (first 15) ---")
for sl, info in sorted(slugs.items())[:15]:
    status = "OK" if info['eps'] > 0 and info['cover'] else "PARTIAL"
    print(f"  {sl}: {info['eps']} eps, cover={'Y' if info['cover'] else 'N'} [{status}]")
if len(slugs) > 15:
    print(f"  ... and {len(slugs)-15} more")

# Incomplete dramas (no episodes)
no_eps = [sl for sl, info in slugs.items() if info['eps'] == 0]
if no_eps:
    print(f"\n--- Dramas with 0 episodes: {len(no_eps)} ---")
    for sl in sorted(no_eps)[:5]:
        print(f"  {sl}")
