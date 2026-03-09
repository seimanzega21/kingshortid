"""
Cleanup: delete all ep_*_thumb.jpg from R2 freereels/ prefix.
Run once to remove thumbnails already uploaded.
"""
import sys, boto3
from botocore.config import Config

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'

r2 = boto3.client('s3', endpoint_url=R2_ENDPOINT,
                  aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                  config=Config(signature_version='s3v4'), region_name='auto')

# Find all thumb files
thumbs = []
token = None
while True:
    kw = {'Bucket': R2_BUCKET, 'Prefix': 'freereels/', 'MaxKeys': 1000}
    if token: kw['ContinuationToken'] = token
    resp = r2.list_objects_v2(**kw)
    thumbs += [o['Key'] for o in resp.get('Contents', []) if '_thumb.jpg' in o['Key']]
    token = resp.get('NextContinuationToken')
    if not token: break

print(f'Found {len(thumbs)} thumb files to delete')

# Delete in batches of 1000
for i in range(0, len(thumbs), 1000):
    batch = thumbs[i:i+1000]
    r2.delete_objects(Bucket=R2_BUCKET, Delete={'Objects': [{'Key': k} for k in batch]})
    print(f'Deleted {len(batch)} thumb files')

print('Done')
