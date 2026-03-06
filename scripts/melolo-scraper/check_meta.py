#!/usr/bin/env python3
"""Check metadata of partial dramas stored in R2"""
import boto3, os, json
from dotenv import load_dotenv
load_dotenv()

s3 = boto3.client('s3',
    endpoint_url=os.getenv('R2_ENDPOINT'),
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'))
bucket = os.getenv('R2_BUCKET_NAME')

slugs_to_check = [
    '800-ribu-beli-dunia-kultivasi',
    'ahli-pengobatan-sakti',
    'dewa-mahjong',
    'dari-miskin-jadi-sultan',
    'mata-tembus-pandang',
]

for sl in slugs_to_check:
    key = f"melolo/{sl}/metadata.json"
    try:
        obj = s3.get_object(Bucket=bucket, Key=key)
        meta = json.loads(obj['Body'].read().decode('utf-8'))
        title = meta.get("title", "?")
        vid = meta.get("vidramaId", "?")
        total = meta.get("totalEpisodes", "?")
        print(f"{sl}:")
        print(f"  Title: {title}")
        print(f"  VidramaId: {vid}")
        print(f"  TotalEpisodes: {total}")
        print()
    except Exception as e:
        print(f"{sl}: ERROR - {e}")
        print()
