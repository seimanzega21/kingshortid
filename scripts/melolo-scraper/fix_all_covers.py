#!/usr/bin/env python3
"""
Fix ALL broken cover.jpg files on R2.
Re-downloads from Vidrama and converts to proper JPEG using Pillow.
"""
import boto3, os, requests, io, json
from dotenv import load_dotenv
from PIL import Image
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except:
    pass

load_dotenv()

s3 = boto3.client('s3',
    endpoint_url=os.getenv('R2_ENDPOINT'),
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'))

BUCKET = os.getenv('R2_BUCKET_NAME')
R2_PUBLIC = "https://stream.shortlovers.id"
API_URL = "https://vidrama.asia/api/melolo"

def download_and_convert_to_jpg(image_url):
    """Download image from any format and convert to JPEG bytes."""
    urls_to_try = [image_url]
    
    # Extract original URL from wsrv.nl proxy
    if "wsrv" in image_url:
        from urllib.parse import urlparse, parse_qs
        qs = parse_qs(urlparse(image_url).query)
        if "url" in qs:
            urls_to_try.insert(0, qs["url"][0])
    
    for url in urls_to_try:
        try:
            resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code != 200 or len(resp.content) < 500:
                continue
            
            # Convert to JPEG using Pillow (handles HEIC, WebP, PNG, etc.)
            img = Image.open(io.BytesIO(resp.content))
            img = img.convert("RGB")  # Ensure RGB mode for JPEG
            
            # Resize if too large (max 800px wide for covers)
            if img.width > 800:
                ratio = 800 / img.width
                img = img.resize((800, int(img.height * ratio)), Image.LANCZOS)
            
            # Save as JPEG
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=85, optimize=True)
            buf.seek(0)
            return buf.getvalue()
        except Exception as e:
            continue
    
    return None

def get_vidrama_covers():
    """Search Vidrama for all dramas and get their cover URLs."""
    all_dramas = {}
    keywords = ["a", "e", "i", "o", "u", "s", "k", "p", "b", "c",
                "d", "m", "r", "n", "t", "l", "g", "h", "j", "w"]
    for kw in keywords:
        try:
            r = requests.get(f"{API_URL}?action=search&keyword={kw}&limit=50", timeout=15)
            if r.status_code == 200:
                for d in r.json().get("data", []):
                    did = d.get("id", "")
                    if did and did not in all_dramas:
                        all_dramas[did] = d
        except:
            pass
    return list(all_dramas.values())

# Get all drama slugs on R2
print("Scanning R2 for drama folders...")
r2_slugs = set()
paginator = s3.get_paginator('list_objects_v2')
for page in paginator.paginate(Bucket=BUCKET, Prefix='melolo/', Delimiter='/'):
    for cp in page.get('CommonPrefixes', []):
        slug = cp['Prefix'].replace('melolo/', '').rstrip('/')
        r2_slugs.add(slug)

print(f"Found {len(r2_slugs)} drama folders on R2\n")

# Get Vidrama covers
print("Fetching cover URLs from Vidrama...")
vidrama_dramas = get_vidrama_covers()
print(f"Found {len(vidrama_dramas)} dramas on Vidrama\n")

# Build slug → image URL mapping
import re
def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return re.sub(r'-+', '-', text).strip('-')

slug_to_image = {}
for d in vidrama_dramas:
    slug = slugify(d["title"])
    img = d.get("image") or d.get("poster", "")
    if img:
        slug_to_image[slug] = img

# Fix covers for all R2 dramas
fixed = 0
failed = 0
skipped = 0

for slug in sorted(r2_slugs):
    key = f'melolo/{slug}/cover.jpg'
    
    # Check current cover
    needs_fix = False
    try:
        obj = s3.head_object(Bucket=BUCKET, Key=key)
        ct = obj.get('ContentType', '')
        size = obj['ContentLength']
        
        # Needs fix if: wrong content-type, too small, or not image/jpeg
        if ct != 'image/jpeg' or size < 1000:
            needs_fix = True
        else:
            # Download and check magic bytes
            obj2 = s3.get_object(Bucket=BUCKET, Key=key)
            first_bytes = obj2['Body'].read(4)
            if first_bytes[:2] != b'\xff\xd8':  # Not JPEG
                needs_fix = True
    except:
        needs_fix = True  # Cover doesn't exist
    
    if not needs_fix:
        skipped += 1
        continue
    
    # Find cover URL from Vidrama
    image_url = slug_to_image.get(slug)
    if not image_url:
        print(f"  {slug}: ❌ no Vidrama match")
        failed += 1
        continue
    
    # Download and convert
    jpg_data = download_and_convert_to_jpg(image_url)
    if not jpg_data:
        print(f"  {slug}: ❌ download/convert failed")
        failed += 1
        continue
    
    # Upload proper JPEG
    s3.put_object(
        Bucket=BUCKET,
        Key=key,
        Body=jpg_data,
        ContentType='image/jpeg',
    )
    print(f"  {slug}: ✅ fixed ({len(jpg_data)//1024}KB JPEG)")
    fixed += 1

print(f"\n{'='*50}")
print(f"  Fixed: {fixed} | Skipped (OK): {skipped} | Failed: {failed}")
print(f"{'='*50}")
