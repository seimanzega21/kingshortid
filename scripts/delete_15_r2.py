import requests, json, time, os
import boto3
from dotenv import load_dotenv

env_path = r'd:\kingshortid\cf-backend\.env.production'
env_vars = {}
with open(env_path, 'r') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            key, val = line.split('=', 1)
            env_vars[key.strip()] = val.strip().strip('"').strip("'")

admin_key = env_vars.get('ADMIN_API_KEY')

# Load R2 credentials from scraper env
load_dotenv(r'd:\kingshortid\scripts\melolo-scraper\.env')
s3 = boto3.client('s3', 
    endpoint_url=os.getenv('R2_ENDPOINT'), 
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'), 
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY')
)
BUCKET = 'shortlovers'

url = 'https://api.shortlovers.id/api/admin/system/delete-small-dramas'
headers = {
    'x-admin-key': admin_key,
    'Content-Type': 'application/json'
}

print('Calling backend to delete from database...')
try:
    r = requests.post(url, headers=headers, json={"maxEpisodes": 15}, timeout=60)
    data = r.json()
    print('DB Status:', r.status_code)
    print(f"Message: {data.get('message')}")
    
    deleted_dramas = data.get('deleted', [])
    if deleted_dramas:
        print(f"Deleting {len(deleted_dramas)} folders from R2...")
        for d in deleted_dramas:
            cover_url = d.get('cover', '')
            if not cover_url: continue
            
            # e.g. https://stream.shortlovers.id/melolo/title-slug/cover.webp
            # We want to extract 'melolo/title-slug/'
            try:
                # Remove https://stream.shortlovers.id/
                path = cover_url.split('.id/')[-1]
                # prefix is everything up to the last slash + slash
                prefix = path.rsplit('/', 1)[0] + '/'
                
                print(f"  -> R2 Prefix: {prefix} ({d['title']})")
                
                # List and delete all objects in prefix
                paginator = s3.get_paginator('list_objects_v2')
                pages = paginator.paginate(Bucket=BUCKET, Prefix=prefix)
                
                count = 0
                for page in pages:
                    objects = page.get('Contents', [])
                    if not objects: continue
                    delete_keys = [{'Key': obj['Key']} for obj in objects]
                    s3.delete_objects(Bucket=BUCKET, Delete={'Objects': delete_keys})
                    count += len(delete_keys)
                    
                print(f"     Deleted {count} files.")
            except Exception as e:
                print(f"  Failed to delete R2 files for {d['title']}: {e}")
                
except Exception as e:
    print('Error:', e)
