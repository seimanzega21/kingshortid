import os, boto3
from botocore.config import Config

R2_ENDPOINT = 'https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com'
R2_KEY_ID   = '07c99c897986ea52703c1285308d5e2c'
R2_SECRET   = '44788d376ffb216e1e73784b6fe1ff1423607928898a87c50819b52cdfc12e44'
R2_BUCKET   = 'shortlovers'

TARGET_DIR = r"D:\KingshortId\Download Drama\Salah Sangka Berujung Jadi Ayah"

s3 = boto3.client('s3', endpoint_url=R2_ENDPOINT,
                  aws_access_key_id=R2_KEY_ID, aws_secret_access_key=R2_SECRET,
                  config=Config(signature_version='s3v4'), region_name='auto')

slugs = [
    'salah-sangka-berujung-jadi-ayah',
    'salah-sangka',
    'salah_sangka',
]

prefixes_to_try = []
for slug in slugs:
    prefixes_to_try.extend([
        f"freereels/{slug}/",
        f"dramas/microdrama/{slug}/",
        f"dramas/dubbing/{slug}/",
        f"netshort/{slug}/"
    ])

found_prefix = None
for prefix in prefixes_to_try:
    res = s3.list_objects_v2(Bucket=R2_BUCKET, Prefix=prefix, MaxKeys=5)
    if 'Contents' in res:
        found_prefix = prefix
        print(f"Found prefix: {prefix}")
        break

if not found_prefix:
    print("Drama not found with expected slugs. Attempting a broader prefix scan...")
    # Just list top level folders under dramas/microdrama/ to find it
    res = s3.list_objects_v2(Bucket=R2_BUCKET, Prefix='dramas/microdrama/', Delimiter='/')
    for p in res.get('CommonPrefixes', []):
        if 'salah' in p['Prefix'] and 'ayah' in p['Prefix']:
            found_prefix = p['Prefix']
            break

if not found_prefix:
    res = s3.list_objects_v2(Bucket=R2_BUCKET, Prefix='freereels/', Delimiter='/')
    for p in res.get('CommonPrefixes', []):
        if 'salah' in p['Prefix'] and 'ayah' in p['Prefix']:
            found_prefix = p['Prefix']
            break

if not found_prefix:
    print("Drama truly not found!")
    exit(1)

print(f"Proceeding to download from {found_prefix} to {TARGET_DIR}")
os.makedirs(TARGET_DIR, exist_ok=True)

# Paginate to get all episodes
paginator = s3.get_paginator('list_objects_v2')
pages = paginator.paginate(Bucket=R2_BUCKET, Prefix=found_prefix)

count = 0
for page in pages:
    for obj in page.get('Contents', []):
        key = obj['Key']
        # Only download high quality .mp4, skip 540p or m3u8
        if key.endswith('.mp4') and not key.endswith('_540p.mp4'):
            # Determine a nice filename
            # e.g., dramas/microdrama/slug/ep001/video.mp4 -> ep001.mp4
            # e.g., freereels/slug/ep001.mp4 -> ep001.mp4
            parts = key.split('/')
            filename = parts[-1]
            if filename == 'video.mp4':
                filename = f"{parts[-2]}.mp4"
            
            out_path = os.path.join(TARGET_DIR, filename)
            if not os.path.exists(out_path):
                print(f"Downloading {filename}...")
                s3.download_file(R2_BUCKET, key, out_path)
                count += 1
            else:
                print(f"Skipping {filename}, already exists.")

print(f"Done! Downloaded {count} episodes.")
