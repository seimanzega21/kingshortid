import boto3
from botocore.config import Config

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

prefix = 'melolo/anak-fana-penakluk-langit/'
print(f"Listing R2 files under prefix '{prefix}':")

paginator = r2.get_paginator('list_objects_v2')
total_files = 0
v540_count = 0
v720_count = 0
mp4_count = 0
other_files = []

for page in paginator.paginate(Bucket=BUCKET, Prefix=prefix):
    for obj in page.get('Contents', []):
        total_files += 1
        key = obj['Key']
        size = obj['Size'] / (1024 * 1024) # MB
        
        if '_540p' in key.lower():
            v540_count += 1
        elif '_720p' in key.lower():
            v720_count += 1
        elif key.lower().endswith('.mp4'):
            mp4_count += 1
            
        if total_files <= 10 or '_540p' in key.lower() or 'cover' in key.lower():
            print(f"  {key} ({size:.2f} MB)")
            
print(f"\nSummary:")
print(f"  Total files in R2: {total_files}")
print(f"  MP4 files: {mp4_count}")
print(f"  Files with '_540p': {v540_count}")
print(f"  Files with '_720p': {v720_count}")
