"""
Delete numbered drama folders from R2 and reorganize structure
"""
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

# R2 credentials
R2_ENDPOINT = os.getenv('R2_ENDPOINT')
R2_ACCESS_KEY = os.getenv('R2_ACCESS_KEY_ID')
R2_SECRET_KEY = os.getenv('R2_SECRET_ACCESS_KEY')
R2_BUCKET = os.getenv('R2_BUCKET_NAME')

# Extract account ID from endpoint
account_id = R2_ENDPOINT.split('//')[1].split('.')[0]

s3 = boto3.client(
    's3',
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY,
    region_name='auto'
)

print("=== CLEANING R2 BUCKET ===\n")

# List all objects in R2
response = s3.list_objects_v2(Bucket=R2_BUCKET)

if 'Contents' not in response:
    print("No objects found in bucket")
    exit()

# Group objects by prefix
from collections import defaultdict
prefixes = defaultdict(list)

for obj in response['Contents']:
    key = obj['Key']
    # Get first folder
    if '/' in key:
        prefix = key.split('/')[0]
        prefixes[prefix].append(key)

print(f"Found {len(prefixes)} top-level folders:\n")
for prefix in sorted(prefixes.keys()):
    count = len(prefixes[prefix])
    print(f"  {prefix}/ ({count} objects)")

# Identify folders to delete (numbered BookIDs)
folders_to_delete = []
for prefix in prefixes.keys():
    # Check if folder name is all digits (BookID)
    if prefix.isdigit() and prefix.startswith('3100'):
        folders_to_delete.append(prefix)

print(f"\n=== Folders to DELETE (numbered BookIDs without videos) ===\n")
for folder in folders_to_delete:
    print(f"  - {folder}/ ({len(prefixes[folder])} objects)")

if folders_to_delete:
    confirm = input(f"\nDelete {len(folders_to_delete)} folders? (yes/no): ")
    
    if confirm.lower() == 'yes':
        for folder in folders_to_delete:
            print(f"\nDeleting {folder}/...")
            
            # Delete all objects in this folder
            for key in prefixes[folder]:
                s3.delete_object(Bucket=R2_BUCKET, Key=key)
                print(f"  Deleted: {key}")
            
            print(f"✅ Deleted {folder}/ ({len(prefixes[folder])} objects)")
        
        print(f"\n🎉 Cleanup complete! Deleted {len(folders_to_delete)} folders")
    else:
        print("Cancelled")
else:
    print("\n✅ No numbered folders to delete")
