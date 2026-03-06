#!/usr/bin/env python3
"""Quick R2 audit: count all dramas, files, episodes, sizes."""
import os, boto3, json, io, sys
from pathlib import Path
from dotenv import load_dotenv

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

paginator = s3.get_paginator('list_objects_v2')
dramas = {}
total_files = 0
total_bytes = 0

for page in paginator.paginate(Bucket=bucket, Prefix='melolo/'):
    for obj in page.get('Contents', []):
        key = obj['Key']
        parts = key.split('/')
        if len(parts) >= 3:
            slug = parts[1]
            if slug not in dramas:
                dramas[slug] = {
                    'files': 0, 'video_eps': 0, 'hls_segments': 0,
                    'bytes': 0, 'has_cover': False, 'has_meta': False,
                    'mp4_count': 0
                }
            d = dramas[slug]
            d['files'] += 1
            d['bytes'] += obj['Size']
            total_files += 1
            total_bytes += obj['Size']
            fname = parts[-1]
            if 'cover' in fname:
                d['has_cover'] = True
            if 'metadata' in fname:
                d['has_meta'] = True
            if fname.endswith('.mp4'):
                d['mp4_count'] += 1
            if fname.endswith('.ts'):
                d['hls_segments'] += 1
            if fname.endswith('.m3u8'):
                d['video_eps'] += 1

gb = total_bytes / (1024 ** 3)
print(f"R2 AUDIT: {len(dramas)} dramas | {total_files} files | {gb:.2f} GB")
print()

for slug in sorted(dramas.keys()):
    d = dramas[slug]
    cover = "C" if d['has_cover'] else " "
    meta = "M" if d['has_meta'] else " "
    eps = d['video_eps'] if d['video_eps'] > 0 else d['mp4_count']
    mb = d['bytes'] / (1024 ** 2)
    fmt = "MP4" if d['mp4_count'] > 0 else "HLS"
    print(f"  [{cover}{meta}] {slug}: {eps} eps ({fmt}), {d['files']} files, {mb:.1f}MB")
