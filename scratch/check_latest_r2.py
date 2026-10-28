import boto3
import os

s3 = boto3.client(
    's3',
    endpoint_url='https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com',
    aws_access_key_id='07c99c897986ea52703c1285308d5e2c',
    aws_secret_access_key='44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44',
    region_name='auto'
)

res = s3.list_objects_v2(
    Bucket='shortlovers',
    Prefix='dramas/covers/'
)

contents = res.get('Contents', [])
# Sort by LastModified descending
contents.sort(key=lambda x: x['LastModified'], reverse=True)

print("=== LATEST 10 OBJECTS IN dramas/covers/ ===")
for obj in contents[:10]:
    print(f"{obj['LastModified']} - {obj['Size']} bytes - {obj['Key']}")
