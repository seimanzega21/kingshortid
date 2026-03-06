#!/usr/bin/env python3
"""Convert HEIC cover images on R2 to actual WebP format.

Downloads each cover, checks if it's HEIC, converts to WebP using pillow-heif,
and re-uploads with correct Content-Type.
"""
import boto3, os, io
from dotenv import load_dotenv
from PIL import Image
import pillow_heif

# Register HEIF opener with Pillow
pillow_heif.register_heif_opener()

load_dotenv()

s3 = boto3.client('s3',
    endpoint_url=os.getenv('R2_ENDPOINT'),
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
    region_name='auto'
)
BUCKET = 'shortlovers'

COVER_EXTENSIONS = {'.webp', '.jpg', '.jpeg', '.png'}

def is_heic(data):
    """Check if raw bytes are HEIC/HEIF format."""
    # ftyp box at offset 4
    if len(data) < 12:
        return False
    return data[4:8] == b'ftyp' and data[8:12] in (b'heic', b'heis', b'hevc', b'hevx', b'mif1', b'msf1')

def main():
    print("=" * 60)
    print("  HEIC → WebP Cover Converter")
    print("=" * 60)

    # Scan for cover files
    print("\n[1] Scanning R2 for cover files...")
    covers = []
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=BUCKET, Prefix='melolo/'):
        for obj in page.get('Contents', []):
            key = obj['Key']
            basename = os.path.basename(key).lower()
            ext = os.path.splitext(basename)[1]
            if (basename.startswith('cover') or basename.startswith('poster')) and ext in COVER_EXTENSIONS:
                covers.append(key)
    
    # Also check vidrama/ prefix
    for page in paginator.paginate(Bucket=BUCKET, Prefix='vidrama/'):
        for obj in page.get('Contents', []):
            key = obj['Key']
            basename = os.path.basename(key).lower()
            ext = os.path.splitext(basename)[1]
            if (basename.startswith('cover') or basename.startswith('poster')) and ext in COVER_EXTENSIONS:
                covers.append(key)

    print(f"  Found {len(covers)} cover files")

    # Process
    print(f"\n[2] Checking and converting HEIC covers...")
    converted = 0
    skipped = 0
    errors = 0

    for i, key in enumerate(covers):
        try:
            response = s3.get_object(Bucket=BUCKET, Key=key)
            data = response['Body'].read()

            if not is_heic(data):
                skipped += 1
                continue

            # Convert HEIC → WebP
            img = Image.open(io.BytesIO(data))
            buf = io.BytesIO()
            img.save(buf, format='WEBP', quality=85)
            webp_data = buf.getvalue()

            # Upload converted WebP (keep same key)
            new_key = os.path.splitext(key)[0] + '.webp'
            s3.put_object(
                Bucket=BUCKET,
                Key=new_key,
                Body=webp_data,
                ContentType='image/webp',
                CacheControl='public, max-age=31536000',
            )

            # Delete old key if different
            if new_key != key:
                s3.delete_object(Bucket=BUCKET, Key=key)

            drama = key.split('/')[1]
            old_kb = len(data) // 1024
            new_kb = len(webp_data) // 1024
            print(f"  ✓ {drama}: HEIC({old_kb}KB) → WebP({new_kb}KB)")
            converted += 1

        except Exception as e:
            drama = key.split('/')[1]
            print(f"  ✗ {drama}: {e}")
            errors += 1

        if (i + 1) % 50 == 0:
            print(f"  ...{i+1}/{len(covers)} processed ({converted} converted)")

    print(f"\n{'=' * 60}")
    print(f"  DONE: Converted={converted}, Skipped={skipped}, Errors={errors}")
    print(f"  Total: {len(covers)}")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    main()
