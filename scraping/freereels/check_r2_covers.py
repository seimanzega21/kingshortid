"""Check actual R2 cover files for dubbing dramas"""
import boto3, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

R2_ENDPOINT = 'https://49c93e6d6787caa7f4e33eacd26e0e00.r2.cloudflarestorage.com'
R2_KEY_ID = '4903f00cc0c17c612b94cddfef8a81fd'
R2_SECRET = 'b879a3d1335ecc92da54de0d48fb7fbec2dca5c6e66c8bad5a319e6fec5e1c6f'
R2_BUCKET = 'shortlovers-stream'
R2_PUBLIC = 'https://stream.shortlovers.id'

s3 = boto3.client('s3',
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_KEY_ID,
    aws_secret_access_key=R2_SECRET,
    region_name='auto',
)

# List all cover files in freereels/
print('Searching for cover files in R2 freereels/...\n')
paginator = s3.get_paginator('list_objects_v2')
covers = []
for page in paginator.paginate(Bucket=R2_BUCKET, Prefix='freereels/'):
    for obj in page.get('Contents', []):
        key = obj['Key']
        if 'cover' in key.lower() or key.endswith('.jpg') or key.endswith('.webp') or key.endswith('.png'):
            covers.append(key)
            print(f'  {key} ({obj["Size"]} bytes)')

print(f'\nTotal cover-like files: {len(covers)}')

# Also check folders
print('\nAll freereels/ folders:')
for page in paginator.paginate(Bucket=R2_BUCKET, Prefix='freereels/', Delimiter='/'):
    for prefix in page.get('CommonPrefixes', []):
        folder = prefix['Prefix']
        # Check for any files in this folder
        sub = s3.list_objects_v2(Bucket=R2_BUCKET, Prefix=folder, MaxKeys=5)
        files = [c['Key'].split('/')[-1] for c in sub.get('Contents', [])]
        print(f'  {folder} -> {files}')
