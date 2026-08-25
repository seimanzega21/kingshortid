import requests, os
from dotenv import load_dotenv
import boto3

load_dotenv(r'd:\kingshortid\cf-backend\.env.production')
api_key = os.getenv('ADMIN_API_KEY')
headers = {'x-admin-key': api_key}

# Load R2 configuration
load_dotenv(r'd:\kingshortid\scripts\melolo-scraper\.env')
s3 = boto3.client('s3',
    endpoint_url=os.getenv('R2_ENDPOINT'),
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
    region_name='auto'
)
bucket = os.getenv('R2_BUCKET_NAME')

print("Fetching pending dramas...")
r = requests.get('http://141.11.160.187:3000/api/dramas?includeInactive=true&limit=5000', headers=headers)
dramas = r.json().get('dramas', [])
pending = [d for d in dramas if not d.get('isActive')]

print(f"Found {len(pending)} pending dramas. Starting deletion...")

for d in pending:
    db_id = d.get('id')
    title = d.get('title')
    cover = d.get('cover') or ''
    print(f"Processing: {title} (ID: {db_id})")
    
    # Delete from DB
    try:
        del_r = requests.delete(f"http://141.11.160.187:3000/api/dramas/{db_id}", headers=headers, timeout=20)
        if del_r.status_code in [200, 204]:
            print("  -> DB Delete: OK")
        else:
            print(f"  -> DB Delete: FAILED ({del_r.status_code}) - {del_r.text}")
    except Exception as e:
        print(f"  -> DB Delete: ERROR ({e})")
        
    # Delete from R2
    if cover and 'stream.shortlovers.id/' in cover:
        # cover url format: https://stream.shortlovers.id/melolo/slug/cover.jpg
        # prefix is: melolo/slug/
        prefix_str = cover.split('stream.shortlovers.id/')[1]
        # split by / and take all parts except the last one (filename)
        parts = prefix_str.split('/')
        if len(parts) >= 2:
            prefix = '/'.join(parts[:-1]) + '/'
            print(f"  -> R2 Prefix to delete: {prefix}")
            
            # List objects
            try:
                paginator = s3.get_paginator('list_objects_v2')
                pages = paginator.paginate(Bucket=bucket, Prefix=prefix)
                delete_us = dict(Objects=[])
                for item in pages.search('Contents'):
                    if item:
                        delete_us['Objects'].append(dict(Key=item['Key']))
                
                if delete_us['Objects']:
                    # Delete objects
                    s3.delete_objects(Bucket=bucket, Delete=delete_us)
                    print(f"  -> R2 Delete: OK ({len(delete_us['Objects'])} objects deleted)")
                else:
                    print("  -> R2 Delete: No objects found")
            except Exception as e:
                print(f"  -> R2 Delete: ERROR ({e})")
        else:
            print(f"  -> R2 Delete: Could not determine prefix from {cover}")

print("Done.")
