import boto3
from pathlib import Path

# R2 Config
R2_ENDPOINT = "https://a142d3b29a5d64943cb251157e25eaf3.r2.cloudflarestorage.com"
R2_ACCESS_KEY = "0e4c9b2e8575f0768b06a379f66235a8"
R2_SECRET_KEY = "408927176624f9c5c747f68e0223852e62fb69664ab18a905d0c81e08b9dc903"
R2_BUCKET = "kingshort"

def delete_all_objects():
    print(f"Connecting to R2 Bucket: {R2_BUCKET}...")
    
    s3 = boto3.client(
        's3',
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        region_name='auto'
    )
    
    # List objects
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=R2_BUCKET, Prefix='goodshort/')
    
    objects_to_delete = []
    
    for page in pages:
        if 'Contents' in page:
            for obj in page['Contents']:
                objects_to_delete.append({'Key': obj['Key']})
    
    if not objects_to_delete:
        print("✅ Bucket is already empty (no objects found with prefix 'goodshort/').")
        return
    
    print(f"⚠️  Found {len(objects_to_delete)} objects to delete.")
    
    # Batch delete (max 1000 per request)
    batch_size = 1000
    for i in range(0, len(objects_to_delete), batch_size):
        batch = objects_to_delete[i:i+batch_size]
        print(f"    Deleting batch {i}-{i+len(batch)}...")
        
        response = s3.delete_objects(
            Bucket=R2_BUCKET,
            Delete={
                'Objects': batch,
                'Quiet': True
            }
        )
        
    print("✅ Deletion complete!")

if __name__ == "__main__":
    delete_all_objects()
