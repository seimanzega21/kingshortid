#!/usr/bin/env python3
"""Fix content-type for all cover images in R2.

Scans all cover files (cover.webp, cover.jpg, poster.jpg, etc.)
in the shortlovers bucket and updates their Content-Type metadata
based on actual file extension and magic bytes.
"""
import boto3, os, sys
from dotenv import load_dotenv

load_dotenv()

s3 = boto3.client('s3',
    endpoint_url=os.getenv('R2_ENDPOINT'),
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'),
    region_name='auto'
)
BUCKET = 'shortlovers'

EXTENSION_MAP = {
    '.webp': 'image/webp',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
}

# Magic byte signatures
MAGIC_BYTES = {
    b'RIFF': 'image/webp',  # RIFF....WEBP
    b'\xff\xd8\xff': 'image/jpeg',
    b'\x89PNG': 'image/png',
    b'GIF8': 'image/gif',
}

def detect_type_from_bytes(data):
    for magic, ct in MAGIC_BYTES.items():
        if data[:len(magic)] == magic:
            return ct
    return None

def get_content_type(key, head_response):
    """Determine correct content-type from extension, then verify with magic bytes."""
    ext = os.path.splitext(key)[1].lower()
    return EXTENSION_MAP.get(ext, 'image/jpeg')

def main():
    print("=" * 60)
    print("  R2 Cover Content-Type Fixer")
    print("=" * 60)
    
    # Find all cover files
    print("\n[1] Scanning R2 for cover files...")
    covers = []
    paginator = s3.get_paginator('list_objects_v2')
    
    for page in paginator.paginate(Bucket=BUCKET, Prefix='melolo/'):
        for obj in page.get('Contents', []):
            key = obj['Key']
            basename = os.path.basename(key).lower()
            if basename.startswith(('cover', 'poster')) and any(basename.endswith(e) for e in EXTENSION_MAP):
                covers.append(key)
    
    print(f"  Found {len(covers)} cover files")
    
    if not covers:
        print("  No covers to fix!")
        return
    
    # Check and fix each cover
    print(f"\n[2] Checking and fixing content types...")
    fixed = 0
    already_ok = 0
    errors = 0
    
    for i, key in enumerate(covers):
        try:
            head = s3.head_object(Bucket=BUCKET, Key=key)
            current_ct = head.get('ContentType', 'unknown')
            correct_ct = get_content_type(key, head)
            
            if current_ct == correct_ct:
                already_ok += 1
                continue
            
            # Fix by copy-in-place with new metadata
            s3.copy_object(
                Bucket=BUCKET,
                Key=key,
                CopySource={'Bucket': BUCKET, 'Key': key},
                ContentType=correct_ct,
                MetadataDirective='REPLACE',
                CacheControl='public, max-age=31536000',
            )
            fixed += 1
            print(f"  ✓ {key}: {current_ct} → {correct_ct}")
            
        except Exception as e:
            errors += 1
            print(f"  ✗ {key}: {e}")
        
        if (i + 1) % 50 == 0:
            print(f"  ...processed {i+1}/{len(covers)} ({fixed} fixed, {already_ok} ok)")
    
    print(f"\n{'=' * 60}")
    print(f"  DONE: Fixed={fixed}, Already OK={already_ok}, Errors={errors}")
    print(f"  Total processed: {len(covers)}")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    main()
