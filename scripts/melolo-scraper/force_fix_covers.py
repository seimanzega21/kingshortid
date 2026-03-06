#!/usr/bin/env python3
"""
Force-fix covers: delete old → re-download → convert to JPEG → upload with explicit content-type.
"""
import boto3, os, requests, io
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

def search_vidrama(keyword):
    r = requests.get(f"{API_URL}?action=search&keyword={keyword}&limit=10", timeout=15)
    return r.json().get("data", []) if r.status_code == 200 else []

# Covers to fix
targets = [
    ("romansa-setelah-pernikahan", "Romansa Setelah"),
    ("dimanja-habis-habisan-oleh-bos", "Dimanja Habis"),
    ("sulit-digoda", "Sulit Digoda"),
]

for slug, search_kw in targets:
    key = f"melolo/{slug}/cover.jpg"
    print(f"\n{'='*50}")
    print(f"  {slug}")
    
    # Step 1: Check current state
    try:
        head = s3.head_object(Bucket=BUCKET, Key=key)
        print(f"  BEFORE: {head['ContentLength']}B | {head.get('ContentType','?')}")
    except:
        print(f"  BEFORE: not found")
    
    # Step 2: Delete existing
    try:
        s3.delete_object(Bucket=BUCKET, Key=key)
        print(f"  Deleted old cover")
    except:
        pass
    
    # Step 3: Find cover URL from Vidrama
    results = search_vidrama(search_kw)
    image_url = None
    for d in results:
        if search_kw.lower()[:10] in d["title"].lower():
            image_url = d.get("image") or d.get("poster", "")
            print(f"  Found: {d['title']}")
            print(f"  Image URL: {image_url[:80]}...")
            break
    
    if not image_url:
        print(f"  ❌ Not found on Vidrama!")
        continue
    
    # Step 4: Download – try original URL first, then wsrv proxy
    urls_to_try = [image_url]
    if "wsrv" in image_url:
        from urllib.parse import urlparse, parse_qs
        qs = parse_qs(urlparse(image_url).query)
        if "url" in qs:
            urls_to_try.insert(0, qs["url"][0])
    
    raw_data = None
    for url in urls_to_try:
        try:
            print(f"  Downloading: {url[:70]}...")
            resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            print(f"    Status: {resp.status_code} | Size: {len(resp.content)}B | CT: {resp.headers.get('content-type','?')}")
            if resp.status_code == 200 and len(resp.content) > 500:
                raw_data = resp.content
                # Check format
                is_jpg = raw_data[:2] == b'\xff\xd8'
                is_webp = len(raw_data) > 12 and raw_data[8:12] == b'WEBP'
                is_heic = b'ftyp' in raw_data[:20]
                print(f"    Format: {'JPG' if is_jpg else 'WEBP' if is_webp else 'HEIC' if is_heic else 'UNKNOWN'}")
                break
        except Exception as e:
            print(f"    Error: {e}")
    
    if not raw_data:
        print(f"  ❌ Download failed!")
        continue
    
    # Step 5: Convert to JPEG using Pillow
    try:
        img = Image.open(io.BytesIO(raw_data))
        print(f"  Pillow opened: {img.format} {img.size} {img.mode}")
        img = img.convert("RGB")
        
        if img.width > 800:
            ratio = 800 / img.width
            new_size = (800, int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)
            print(f"  Resized to: {new_size}")
        
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85, optimize=True)
        jpg_bytes = buf.getvalue()
        print(f"  Converted to JPEG: {len(jpg_bytes)}B")
        
        # Verify it's actually JPEG
        assert jpg_bytes[:2] == b'\xff\xd8', "Not JPEG!"
    except Exception as e:
        print(f"  ❌ Conversion failed: {e}")
        continue
    
    # Step 6: Upload to R2 with EXPLICIT content-type
    s3.put_object(
        Bucket=BUCKET,
        Key=key,
        Body=jpg_bytes,
        ContentType="image/jpeg",
        CacheControl="public, max-age=31536000",
    )
    print(f"  ✅ Uploaded: {len(jpg_bytes)}B as image/jpeg")
    
    # Step 7: Verify
    head2 = s3.head_object(Bucket=BUCKET, Key=key)
    print(f"  AFTER: {head2['ContentLength']}B | {head2.get('ContentType','?')}")
    
    # Check public URL
    pub_url = f"{R2_PUBLIC}/melolo/{slug}/cover.jpg"
    r = requests.head(pub_url, timeout=5)
    print(f"  Public URL: {r.status_code} | {r.headers.get('content-type','?')} | {r.headers.get('content-length','?')}B")

print(f"\n{'='*50}")
print("DONE! Check R2 dashboard again.")
