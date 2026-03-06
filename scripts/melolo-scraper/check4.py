import boto3, os
from dotenv import load_dotenv
load_dotenv()
s3 = boto3.client('s3', endpoint_url=os.getenv('R2_ENDPOINT'), aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'), aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'))
B = 'shortlovers'

# Search for partial matches of these drama names
search_terms = ['kehadiran', 'mata-kiri', 'hidup-berjaya', 'nona-riley', 'perjalanan-naga']
paginator = s3.get_paginator('list_objects_v2')

# List ALL drama folders on R2
print("Scanning all R2 drama folders...")
folders = set()
for page in paginator.paginate(Bucket=B, Prefix='melolo/', Delimiter='/'):
    for p2 in page.get('CommonPrefixes', []):
        slug = p2['Prefix'].split('/')[1]
        folders.add(slug)

print(f"Total R2 folders: {len(folders)}")

# Search for partial matches
for term in search_terms:
    matches = [f for f in folders if term in f]
    if matches:
        print(f"\n'{term}' matches: {matches}")
    else:
        print(f"\n'{term}': NO MATCH on R2")

# Also check misi-cinta ep URLs in DB
print("\n--- Checking misi-cinta DB URLs ---")
