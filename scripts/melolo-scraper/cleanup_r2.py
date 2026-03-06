#!/usr/bin/env python3
"""
Cleanup incomplete multipart uploads and stale directories on R2.
Run this AFTER stream_to_r2.py and bulk_upload_r2.py have finished.
"""
import os, boto3
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / '.env')

R2_ENDPOINT = os.getenv('R2_ENDPOINT')
R2_ACCESS_KEY_ID = os.getenv('R2_ACCESS_KEY_ID')
R2_SECRET_ACCESS_KEY = os.getenv('R2_SECRET_ACCESS_KEY')
R2_BUCKET = os.getenv('R2_BUCKET_NAME', 'shortlovers')

s3 = boto3.client('s3', endpoint_url=R2_ENDPOINT,
                   aws_access_key_id=R2_ACCESS_KEY_ID,
                   aws_secret_access_key=R2_SECRET_ACCESS_KEY,
                   region_name='auto')

def cleanup_multipart():
    """Abort all incomplete multipart uploads"""
    print("=== Cleaning up incomplete multipart uploads ===\n")
    
    aborted = 0
    paginator = s3.get_paginator('list_multipart_uploads')
    
    try:
        for page in paginator.paginate(Bucket=R2_BUCKET):
            for upload in page.get('Uploads', []):
                key = upload['Key']
                upload_id = upload['UploadId']
                initiated = upload.get('Initiated', '?')
                
                print(f"  Aborting: {key}")
                print(f"    Upload ID: {upload_id}")
                print(f"    Started:   {initiated}")
                
                try:
                    s3.abort_multipart_upload(
                        Bucket=R2_BUCKET,
                        Key=key,
                        UploadId=upload_id
                    )
                    aborted += 1
                    print(f"    ✅ Aborted")
                except Exception as e:
                    print(f"    ❌ Error: {e}")
    except Exception as e:
        print(f"  Error listing uploads: {e}")
    
    print(f"\n  Total aborted: {aborted}")
    return aborted


def cleanup_stale_directories():
    """Remove numbered directories that are residual from failed uploads"""
    print("\n=== Cleaning up stale numbered directories ===\n")
    
    deleted = 0
    paginator = s3.get_paginator('list_objects_v2')
    
    # Look for top-level objects that are just numbers (not under melolo/)
    try:
        for page in paginator.paginate(Bucket=R2_BUCKET, Delimiter='/'):
            for prefix in page.get('CommonPrefixes', []):
                name = prefix['Prefix'].rstrip('/')
                # Check if it's a numeric directory (stale multipart residual)
                if name.isdigit():
                    print(f"  Found stale dir: {name}/")
                    
                    # List and delete all objects inside
                    inner_paginator = s3.get_paginator('list_objects_v2')
                    keys_to_delete = []
                    for inner_page in inner_paginator.paginate(Bucket=R2_BUCKET, Prefix=f"{name}/"):
                        for obj in inner_page.get('Contents', []):
                            keys_to_delete.append(obj['Key'])
                    
                    if keys_to_delete:
                        # Delete in batches of 1000
                        for i in range(0, len(keys_to_delete), 1000):
                            batch = keys_to_delete[i:i+1000]
                            s3.delete_objects(
                                Bucket=R2_BUCKET,
                                Delete={'Objects': [{'Key': k} for k in batch]}
                            )
                        deleted += len(keys_to_delete)
                        print(f"    ✅ Deleted {len(keys_to_delete)} objects")
                    else:
                        print(f"    Empty directory")
    except Exception as e:
        print(f"  Error: {e}")
    
    print(f"\n  Total stale objects deleted: {deleted}")
    return deleted


def main():
    print("=" * 60)
    print("  R2 CLEANUP — Remove incomplete uploads & stale data")
    print("=" * 60)
    
    aborted = cleanup_multipart()
    deleted = cleanup_stale_directories()
    
    print(f"\n{'=' * 60}")
    print(f"  CLEANUP COMPLETE")
    print(f"  Multipart uploads aborted: {aborted}")
    print(f"  Stale objects deleted:     {deleted}")
    print(f"{'=' * 60}")


if __name__ == '__main__':
    main()
