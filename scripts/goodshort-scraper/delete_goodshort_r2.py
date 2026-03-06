"""Delete goodshort/ folder from R2 completely"""
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

print("Deleting goodshort/ folder from R2...\n")

# List and delete all objects with goodshort/ prefix
continuation_token = None
total_deleted = 0

while True:
    if continuation_token:
        response = s3.list_objects_v2(
            Bucket=R2_BUCKET,
            Prefix='goodshort/',
            ContinuationToken=continuation_token
        )
    else:
        response = s3.list_objects_v2(
            Bucket=R2_BUCKET,
            Prefix='goodshort/'
        )
    
    if 'Contents' not in response:
        break
    
    # Delete batch
    objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
    
    if objects_to_delete:
        s3.delete_objects(
            Bucket=R2_BUCKET,
            Delete={'Objects': objects_to_delete}
        )
        total_deleted += len(objects_to_delete)
        print(f"Deleted {len(objects_to_delete)} objects (total: {total_deleted})")
    
    if not response.get('IsTruncated'):
        break
    
    continuation_token = response.get('NextContinuationToken')

print(f"\n✅ Deleted {total_deleted} objects from goodshort/ folder")
