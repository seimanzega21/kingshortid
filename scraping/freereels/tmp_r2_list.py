import boto3
from botocore.config import Config

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'

r2 = boto3.client('s3', endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
    config=Config(signature_version='s3v4'), region_name='auto')

# List first 20 objects in freereels/ prefix
resp = r2.list_objects_v2(Bucket=R2_BUCKET, Prefix='freereels/', MaxKeys=20)
contents = resp.get('Contents', [])
print(f"Objects in freereels/ (first 20):")
for obj in contents:
    print(f"  {obj['Key']} ({obj['Size']/1024/1024:.1f}MB)")

if not contents:
    # Try without prefix
    resp2 = r2.list_objects_v2(Bucket=R2_BUCKET, MaxKeys=20)
    contents2 = resp2.get('Contents', [])
    print(f"\nAll objects (first 20):")
    for obj in contents2:
        print(f"  {obj['Key']} ({obj['Size']/1024:.0f}KB)")
    
    # List common prefixes
    resp3 = r2.list_objects_v2(Bucket=R2_BUCKET, Delimiter='/', MaxKeys=20)
    prefixes = resp3.get('CommonPrefixes', [])
    print(f"\nTop-level prefixes:")
    for p in prefixes:
        print(f"  {p['Prefix']}")
