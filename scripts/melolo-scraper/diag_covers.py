import boto3, os, requests
from dotenv import load_dotenv
load_dotenv()

s3 = boto3.client('s3',
    endpoint_url=os.getenv('R2_ENDPOINT'),
    aws_access_key_id=os.getenv('R2_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('R2_SECRET_ACCESS_KEY'))

BUCKET = os.getenv('R2_BUCKET_NAME')
R2_PUBLIC = "https://stream.shortlovers.id"

# Check newly scraped covers specifically
slugs = ['romansa-setelah-pernikahan', 'dimanja-habis-habisan-oleh-bos', 'sulit-digoda']

for slug in slugs:
    key = f'melolo/{slug}/cover.jpg'
    print(f"\n{slug}:")
    try:
        obj = s3.get_object(Bucket=BUCKET, Key=key)
        body = obj['Body'].read()
        size = len(body)
        ct = obj.get('ContentType', '?')
        
        is_jpg = body[:2] == b'\xff\xd8'
        is_png = body[:4] == b'\x89PNG'
        is_webp = len(body) > 12 and body[8:12] == b'WEBP'
        is_html = b'<html' in body[:200].lower() or b'<!doctype' in body[:200].lower()
        
        fmt = 'JPG' if is_jpg else 'PNG' if is_png else 'WEBP' if is_webp else 'HTML' if is_html else 'UNKNOWN'
        print(f"  R2 size={size}B | content-type={ct} | actual_format={fmt}")
        
        # Show first bytes as text if not binary image
        if not is_jpg and not is_png and not is_webp:
            try:
                print(f"  First 200 chars: {body[:200].decode('utf-8', errors='replace')}")
            except:
                print(f"  First 20 hex: {body[:20].hex()}")
    except Exception as e:
        print(f"  NOT FOUND: {e}")

# Also check an old working cover for comparison
print("\n--- OLD WORKING COVER ---")
old_slug = 'istri-desa-si-kapten'
try:
    obj = s3.get_object(Bucket=BUCKET, Key=f'melolo/{old_slug}/cover.jpg')
    body = obj['Body'].read()
    ct = obj.get('ContentType', '?')
    is_jpg = body[:2] == b'\xff\xd8'
    is_webp = len(body) > 12 and body[8:12] == b'WEBP'
    fmt = 'JPG' if is_jpg else 'WEBP' if is_webp else 'OTHER'
    print(f"  {old_slug}: size={len(body)}B | ct={ct} | format={fmt}")
except Exception as e:
    print(f"  {old_slug}: {e}")
