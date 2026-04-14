import os
import boto3
from dotenv import load_dotenv

load_dotenv('d:\\kingshortid\\cf-backend\\.env.production')

s3 = boto3.client(
    "s3",
    endpoint_url=os.getenv("R2_ENDPOINT"),
    aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
)

bucket = os.getenv("R2_BUCKET", "shortlovers-media")
prefix = "vidrama/microdrama/bangkit-dari-dosa-palsu/"

for i in range(1, 15):
    k1 = f"{prefix}ep{i:03d}.mp4"
    k2 = f"{prefix}ep{i:03d}_540p.mp4"
    print(f"Deleting {k1}...")
    s3.delete_object(Bucket=bucket, Key=k1)
    print(f"Deleting {k2}...")
    s3.delete_object(Bucket=bucket, Key=k2)

print("Done deleting bloated R2 segments.")
