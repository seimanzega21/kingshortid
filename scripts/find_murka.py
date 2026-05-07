import boto3
from botocore.config import Config

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'

r2 = boto3.client('s3', endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
    config=Config(signature_version='s3v4'), region_name='auto')

def list_folders(prefix):
    paginator = r2.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket='shortlovers', Prefix=prefix, Delimiter='/')
    for page in pages:
        if 'CommonPrefixes' in page:
            for cp in page['CommonPrefixes']:
                print(cp['Prefix'])

print("Folders in dramas/:")
list_folders('dramas/')
print("\nRoot folders:")
list_folders('')
