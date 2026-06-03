import boto3
from botocore.config import Config

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'

def list_r2():
    r2 = boto3.client('s3', endpoint_url=R2_ENDPOINT,
                        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                        config=Config(signature_version='s3v4'), region_name='auto')
                        
    prefix = "dramas/mendengar-isi-hatimu/"
    print(f"Listing R2 bucket 'shortlovers' with prefix: '{prefix}'")
    res = r2.list_objects_v2(Bucket='shortlovers', Prefix=prefix)
    contents = res.get('Contents', [])
    print(f"Found {len(contents)} files in R2:")
    for obj in contents:
        print(f"  {obj['Key']} ({obj['Size']} bytes) - LastModified: {obj['LastModified']}")

if __name__ == "__main__":
    list_r2()
