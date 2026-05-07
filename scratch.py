import boto3
from botocore.config import Config
import json

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'

r2 = boto3.client('s3', endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
    config=Config(signature_version='s3v4'), region_name='auto')

id = 'wnvoz8au35dfmw90kcfabu18y'
print(f"Checking prefix '{id}'...")
response = r2.list_objects_v2(Bucket='shortlovers', Prefix=id)
if 'Contents' in response:
    print(f"Found {len(response['Contents'])} objects for '{id}'")
else:
    print(f"No objects found for prefix '{id}'")

print(f"\nChecking prefix 'dramas/{id}'...")
response = r2.list_objects_v2(Bucket='shortlovers', Prefix=f'dramas/{id}')
if 'Contents' in response:
    print(f"Found {len(response['Contents'])} objects for 'dramas/{id}'")
else:
    print(f"No objects found for prefix 'dramas/{id}'")
