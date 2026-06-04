import boto3

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
BUCKET      = 'shortlovers'

r2 = boto3.client(
    's3',
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_KEY_ID,
    aws_secret_access_key=R2_SECRET,
    region_name='auto'
)

prefix = "netshortv2/mencari-sinar-di-lautan/"

print("Listing files in R2 under:", prefix)
paginator = r2.get_paginator('list_objects_v2')
pages = paginator.paginate(Bucket=BUCKET, Prefix=prefix)

vtt_files = []
mp4_files = []

for page in pages:
    for obj in page.get('Contents', []):
        key = obj['Key']
        if key.endswith('.vtt'):
            vtt_files.append(key)
        elif key.endswith('.mp4'):
            mp4_files.append(key)

print(f"Total MP4 files: {len(mp4_files)}")
print(f"Total VTT files: {len(vtt_files)}")
print("\nVTT Files list:")
for k in sorted(vtt_files):
    print("  -", k)
