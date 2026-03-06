#!/usr/bin/env python3
"""
Quick check: verify kaya-raya-di-era-1992 playlists on R2
"""
import boto3, os
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client('s3',
    endpoint_url=os.getenv('R2_ENDPOINT'),
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
    region_name='auto'
)

BUCKET = 'shortlovers'
DRAMA = 'kaya-raya-di-era-1992'

print(f"Checking {DRAMA} on R2...\n")

# Get all files for this drama
prefix = f"melolo/{DRAMA}/episodes/"
files = []

paginator = s3.get_paginator('list_objects_v2')
for page in paginator.paginate(Bucket=BUCKET, Prefix=prefix):
    for obj in page.get('Contents', []):
        files.append(obj['Key'])

# Group by episode
episodes = {}
for f in files:
    parts = f.split('/')
    if len(parts) >= 4:
        ep_num = parts[3]
        if ep_num not in episodes:
            episodes[ep_num] = []
        episodes[ep_num].append(parts[-1])

# Check each episode
print(f"Episodes found: {len(episodes)}\n")

for ep_num in sorted(episodes.keys()):
    files_in_ep = episodes[ep_num]
    has_playlist = any('playlist.m3u8' in f for f in files_in_ep)
    segments = [f for f in files_in_ep if f.endswith('.ts')]
    
    status = "✅" if has_playlist and len(segments) > 0 else "❌"
    
    print(f"{status} Ep {ep_num}: playlist={'✅' if has_playlist else '❌'}, segments={len(segments)}")

print(f"\nTotal episodes: {len(episodes)}")
complete = sum(1 for ep in episodes.values() if any('playlist.m3u8' in f for f in ep))
print(f"Complete (with playlist): {complete}")
