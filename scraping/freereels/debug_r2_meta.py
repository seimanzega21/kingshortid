"""Debug: Read each R2 metadata and show series_id + title for matching"""
import boto3, sys, json
from botocore.config import Config
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'

r2 = boto3.client('s3', endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
    config=Config(signature_version='s3v4'), region_name='auto')

# List and read all metadata.json files  
token = None
meta_keys = []
while True:
    kwargs = {'Bucket': R2_BUCKET, 'Prefix': 'freereels/', 'MaxKeys': 1000}
    if token: kwargs['ContinuationToken'] = token
    resp = r2.list_objects_v2(**kwargs)
    for obj in resp.get('Contents', []):
        if obj['Key'].endswith('/metadata.json'):
            meta_keys.append(obj['Key'])
    token = resp.get('NextContinuationToken')
    if not token: break

print(f'Found {len(meta_keys)} metadata files\n')
print(f'{"Folder":<45} {"series_id":<15} {"title":<40} {"eps":>4}')
print('—' * 110)

for key in sorted(meta_keys):
    try:
        obj = r2.get_object(Bucket=R2_BUCKET, Key=key)
        meta = json.loads(obj['Body'].read().decode('utf-8'))
        folder = key.split('/')[1]
        sid = meta.get('series_id', '?')
        title = meta.get('title', meta.get('titleClean', '?'))
        eps = len([e for e in meta.get('episodes', []) if e.get('uploaded') or e.get('videoUrl')])
        cover = meta.get('cover', 'NO_COVER')
        print(f'{folder:<45} {sid:<15} {title[:40]:<40} {eps:>4}')
    except Exception as e:
        print(f'{key}: ERROR {e}')
