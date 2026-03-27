"""Debug: list all R2 folders under freereels/ to compare with DB FRkeys"""
import boto3, sys
from botocore.config import Config
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'

r2 = boto3.client('s3', endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
    config=Config(signature_version='s3v4'), region_name='auto')

# List metadata.json files
token = None
found = []
while True:
    kwargs = {'Bucket': R2_BUCKET, 'Prefix': 'freereels/', 'MaxKeys': 1000}
    if token: kwargs['ContinuationToken'] = token
    resp = r2.list_objects_v2(**kwargs)
    for obj in resp.get('Contents', []):
        key = obj['Key']
        if key.endswith('/metadata.json'):
            folder = key.split('/')[1] if len(key.split('/')) >= 3 else '?'
            found.append((folder, key))
    token = resp.get('NextContinuationToken')
    if not token: break

print(f'Found {len(found)} metadata.json files:')
for folder, key in sorted(found):
    print(f'  {folder:55s} → {key}')

# Also list top-level folders
print(f'\nTop-level folders via CommonPrefixes:')
token = None
folders = []
while True:
    kwargs = {'Bucket': R2_BUCKET, 'Prefix': 'freereels/', 'Delimiter': '/', 'MaxKeys': 1000}
    if token: kwargs['ContinuationToken'] = token
    resp = r2.list_objects_v2(**kwargs)
    for cp in resp.get('CommonPrefixes', []):
        folders.append(cp['Prefix'])
    token = resp.get('NextContinuationToken')
    if not token: break

for f in sorted(folders):
    print(f'  {f}')
print(f'Total folders: {len(folders)}')
