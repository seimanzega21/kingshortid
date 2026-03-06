import boto3, os, requests, json
from dotenv import load_dotenv
load_dotenv()

s3 = boto3.client('s3',
    endpoint_url=os.getenv('R2_ENDPOINT'),
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'))

# List all folders to find newly uploaded dramas
# We know romansa-setelah-pernikahan is one, find the second
paginator = s3.get_paginator('list_objects_v2')

# Check romansa episodes
r1 = s3.list_objects_v2(Bucket='shortlovers', Prefix='melolo/romansa-setelah-pernikahan/', MaxKeys=50)
print(f"romansa-setelah-pernikahan: {len(r1.get('Contents',[]))} files")

# Find ALL melolo folders and check which have ep001.mp4 (new format)
folders = set()
for page in paginator.paginate(Bucket='shortlovers', Prefix='melolo/', Delimiter='/'):
    for p2 in page.get('CommonPrefixes', []):
        slug = p2['Prefix'].split('/')[1]
        folders.add(slug)

print(f"\nTotal melolo folders: {len(folders)}")

# Find folders that have .mp4 files (new scraper format)
mp4_dramas = []
for slug in sorted(folders):
    r = s3.list_objects_v2(Bucket='shortlovers', Prefix=f'melolo/{slug}/ep001.mp4', MaxKeys=1)
    if r.get('Contents'):
        # Count total MP4s
        r2 = s3.list_objects_v2(Bucket='shortlovers', Prefix=f'melolo/{slug}/ep', MaxKeys=200)
        count = len([o for o in r2.get('Contents',[]) if o['Key'].endswith('.mp4')])
        mp4_dramas.append((slug, count))

print(f"\nDramas with MP4 files:")
for slug, count in mp4_dramas:
    print(f"  {slug}: {count} mp4 episodes")
