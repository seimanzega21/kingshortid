import boto3
from botocore.config import Config

R2_ENDPOINT  = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID    = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET    = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET    = 'shortlovers'

r2 = boto3.client('s3', endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
    config=Config(signature_version='s3v4'), region_name='auto')

res = r2.list_objects_v2(Bucket=R2_BUCKET, Prefix='dramas/')
items = res.get('Contents', [])
folders = set()
for item in items:
    key = item['Key']
    parts = key.split('/')
    if len(parts) > 1:
        folders.add(parts[1])
print("Top level folders in dramas/:", folders)

folders_with_kera = set()
for item in items:
    if 'kera' in item['Key'].lower():
        folders_with_kera.add(item['Key'])

print("Files with 'kera':", folders_with_kera)
