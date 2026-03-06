#!/usr/bin/env python3
import boto3, os, json
from dotenv import load_dotenv
load_dotenv()

s3 = boto3.client("s3",
    endpoint_url=os.getenv("R2_ENDPOINT"),
    aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"))

bucket = os.getenv("R2_BUCKET_NAME")
slug = "kebangkitan-tabib-yang-putus-asa"
prefix = f"melolo/{slug}/"

# List all objects
objs = []
paginator = s3.get_paginator("list_objects_v2")
for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
    objs.extend(page.get("Contents", []))

eps = [o for o in objs if o["Key"].endswith(".mp4")]
other = [o for o in objs if not o["Key"].endswith(".mp4")]

print(f"=== {slug} ===")
print(f"Total files in R2: {len(objs)}")
print(f"Episodes (MP4): {len(eps)}")
print(f"Other files: {len(other)}")

# Show other files  
for o in other:
    name = o["Key"].split("/")[-1]
    print(f"  {name} ({o['Size']/1024:.1f} KB)")

# Show first and last episodes
sorted_eps = sorted(eps, key=lambda x: x["Key"])
if sorted_eps:
    first = sorted_eps[0]["Key"].split("/")[-1]
    last = sorted_eps[-1]["Key"].split("/")[-1]
    print(f"\nFirst episode: {first}")
    print(f"Last episode: {last}")

# Check metadata
try:
    meta = s3.get_object(Bucket=bucket, Key=f"{prefix}metadata.json")
    md = json.loads(meta["Body"].read())
    expected = md.get("totalEpisodes", "?")
    print(f"\nExpected episodes (metadata): {expected}")
    complete = len(eps) >= expected if isinstance(expected, int) else "unknown"
    print(f"Complete: {complete}")
    if isinstance(expected, int) and len(eps) < expected:
        print(f"Missing: {expected - len(eps)} episodes")
except Exception as e:
    print(f"\nNo metadata: {e}")
