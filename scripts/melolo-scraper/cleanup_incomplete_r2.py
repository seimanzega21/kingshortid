#!/usr/bin/env python3
"""
Cleanup incomplete multipart uploads on R2 and re-upload failed files
"""
import boto3, os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client('s3',
    endpoint_url=os.getenv('R2_ENDPOINT'),
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
    region_name='auto'
)

BUCKET = 'shortlovers'
MELOLO_DIR = Path('r2_ready/melolo')

print("=" * 60)
print("  CLEANUP R2 INCOMPLETE UPLOADS")
print("=" * 60)

# 1. List all incomplete multipart uploads
print("\n🔍 Checking for incomplete multipart uploads...")
try:
    response = s3.list_multipart_uploads(Bucket=BUCKET, Prefix='melolo/')
    uploads = response.get('Uploads', [])
    
    if not uploads:
        print("  ✅ No incomplete uploads found")
    else:
        print(f"  ⚠️  Found {len(uploads)} incomplete uploads:\n")
        
        for upload in uploads:
            key = upload['Key']
            upload_id = upload['UploadId']
            initiated = upload['Initiated']
            
            print(f"  - {key}")
            print(f"    Upload ID: {upload_id}")
            print(f"    Started: {initiated}")
            
            # Abort the incomplete upload
            s3.abort_multipart_upload(
                Bucket=BUCKET,
                Key=key,
                UploadId=upload_id
            )
            print(f"    ✅ Aborted\n")
        
        print(f"\n✅ Cleaned up {len(uploads)} incomplete uploads")
        
        # 2. Re-upload the failed files
        print("\n🔄 Re-uploading failed files...\n")
        
        for upload in uploads:
            key = upload['Key']
            # melolo/drama-slug/episodes/001.mp4 -> r2_ready/melolo/drama-slug/episodes/001.mp4
            local_path = MELOLO_DIR / '/'.join(key.split('/')[1:])
            
            if not local_path.exists():
                print(f"  ⚠️  Local file not found: {local_path}")
                continue
            
            # Determine content type
            if local_path.suffix == '.mp4':
                ct = 'video/mp4'
            elif local_path.suffix == '.m3u8':
                ct = 'application/vnd.apple.mpegurl'
            elif local_path.suffix == '.ts':
                ct = 'video/mp2t'
            else:
                ct = 'application/octet-stream'
            
            try:
                print(f"  📤 Uploading: {key}")
                s3.upload_file(
                    str(local_path),
                    BUCKET,
                    key,
                    ExtraArgs={'ContentType': ct}
                )
                print(f"  ✅ Success\n")
            except Exception as e:
                print(f"  ❌ Failed: {e}\n")

except Exception as e:
    print(f"  ❌ Error: {e}")

print("\n" + "=" * 60)
print("  CLEANUP COMPLETE")
print("=" * 60 + "\n")
