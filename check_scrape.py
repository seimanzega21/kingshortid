import boto3
from botocore.config import Config

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'

def check():
    r2 = boto3.client('s3', endpoint_url=R2_ENDPOINT,
                        aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                        config=Config(signature_version='s3v4'), region_name='auto')
    
    slugs = {
        'raja-yang-ditakuti-musuh': 82,
        'menghabisi-yang-jahat': 91,
        'dua-kuasa-menjadi-satu': 102
    }
    
    for slug, total in slugs.items():
        prefix = f"netshortv2/{slug}/"
        res = r2.list_objects_v2(Bucket='shortlovers', Prefix=prefix)
        count = len([obj for obj in res.get('Contents', []) if obj['Key'].endswith('.mp4') and '_540p' not in obj['Key']])
        print(f"{slug}: {count}/{total} episodes ({count/total*100:.0f}%)")

if __name__ == "__main__":
    check()
