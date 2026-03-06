"""
Reorganize R2 structure: Move goodshort/* to root
From: shortlovers/goodshort/Cinta_di_Waktu_yang_Tepat/*
To:   shortlovers/Cinta_di_Waktu_yang_Tepat/*
"""
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

R2_ENDPOINT = os.getenv('R2_ENDPOINT')
R2_ACCESS_KEY = os.getenv('R2_ACCESS_KEY_ID')
R2_SECRET_KEY = os.getenv('R2_SECRET_ACCESS_KEY')
R2_BUCKET = os.getenv('R2_BUCKET_NAME')

s3 = boto3.client(
    's3',
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY,
    region_name='auto'
)

print("=== REORGANIZING R2 STRUCTURE ===\n")
print("Moving goodshort/* to root level...\n")

# List all objects with goodshort/ prefix
response = s3.list_objects_v2(Bucket=R2_BUCKET, Prefix='goodshort/')

if 'Contents' not in response:
    print("No goodshort/ folder found")
    exit()

objects_to_move = response['Contents']
print(f"Found {len(objects_to_move)} objects to move\n")

moved = 0
for obj in objects_to_move:
    old_key = obj['Key']
    
    # Remove 'goodshort/' prefix
    new_key = old_key.replace('goodshort/', '')
    
    if not new_key:  # Skip if becomes empty
        continue
    
    print(f"Moving: {old_key} → {new_key}")
    
    # Copy to new location
    s3.copy_object(
        Bucket=R2_BUCKET,
        CopySource={'Bucket': R2_BUCKET, 'Key': old_key},
        Key=new_key,
        ACL='public-read'
    )
    
    # Delete old object
    s3.delete_object(Bucket=R2_BUCKET, Key=old_key)
    
    moved += 1

print(f"\n✅ Moved {moved} objects")
print(f"🎉 Reorganization complete!")
