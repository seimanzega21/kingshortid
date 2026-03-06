#!/usr/bin/env python3
"""
Fix remaining 25 covers by using DB drama titles to find Vidrama covers.
"""
import boto3, os, requests, io, re, json, subprocess
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
API_URL = "https://vidrama.asia/api/melolo"

def convert_to_jpg(image_data):
    try:
        img = Image.open(io.BytesIO(image_data))
        img = img.convert("RGB")
        if img.width > 800:
            ratio = 800 / img.width
            img = img.resize((800, int(img.height * ratio)), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85, optimize=True)
        buf.seek(0)
        return buf.getvalue()
    except:
        return None

# Get DB dramas with their titles and cover URLs
result = subprocess.run(["node", "-e", """
const {PrismaClient} = require('@prisma/client');
const p = new PrismaClient();
p.drama.findMany({
    where: {isActive: true},
    select: {id: true, title: true, cover: true}
}).then(ds => {
    process.stdout.write(JSON.stringify(ds));
    p.$disconnect();
});
"""], capture_output=True, text=True, cwd=r"D:\kingshortid\admin", timeout=15)

db_dramas = json.loads(result.stdout)
print(f"DB dramas: {len(db_dramas)}")

# Build Vidrama cache (title → image URL)
print("Fetching Vidrama index...")
vidrama_cache = {}
keywords = ["a", "e", "i", "o", "u", "s", "k", "p", "b", "c",
            "d", "m", "r", "n", "t", "l", "g", "h", "j", "w"]
for kw in keywords:
    try:
        r = requests.get(f"{API_URL}?action=search&keyword={kw}&limit=50", timeout=15)
        if r.status_code == 200:
            for d in r.json().get("data", []):
                title = d.get("title", "").strip()
                img = d.get("image") or d.get("poster", "")
                if title and img:
                    vidrama_cache[title.lower()] = img
    except:
        pass
print(f"Vidrama index: {len(vidrama_cache)} dramas\n")

# Find covers that need fixing
fixed = 0
already_ok = 0
failed = 0

for d in db_dramas:
    # Extract slug from cover URL
    cover = d.get("cover", "")
    if not cover:
        continue
    
    # Parse slug from cover URL like https://stream.shortlovers.id/melolo/{slug}/cover.jpg
    m = re.search(r'melolo/([^/]+)/cover\.jpg', cover)
    if not m:
        continue
    slug = m.group(1)
    key = f'melolo/{slug}/cover.jpg'
    
    # Check if cover is already valid JPEG
    try:
        obj = s3.get_object(Bucket=BUCKET, Key=key)
        data = obj['Body'].read()
        if data[:2] == b'\xff\xd8' and len(data) > 1000:
            already_ok += 1
            continue  # Already good JPEG
    except:
        pass  # Cover missing entirely
    
    # Find matching Vidrama cover using DB title
    title = d["title"]
    image_url = vidrama_cache.get(title.lower())
    
    # Try fuzzy match if exact match fails
    if not image_url:
        title_lower = title.lower()
        for vt, vimg in vidrama_cache.items():
            if title_lower[:15] in vt or vt[:15] in title_lower:
                image_url = vimg
                break
    
    if not image_url:
        print(f"  {title}: ❌ no Vidrama match")
        failed += 1
        continue
    
    # Download and convert cover
    urls = [image_url]
    if "wsrv" in image_url:
        from urllib.parse import urlparse, parse_qs
        qs = parse_qs(urlparse(image_url).query)
        if "url" in qs:
            urls.insert(0, qs["url"][0])
    
    jpg_data = None
    for url in urls:
        try:
            resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code == 200 and len(resp.content) > 500:
                jpg_data = convert_to_jpg(resp.content)
                if jpg_data:
                    break
        except:
            continue
    
    if not jpg_data:
        print(f"  {title}: ❌ download/convert failed")
        failed += 1
        continue
    
    # Upload fixed cover
    s3.put_object(Bucket=BUCKET, Key=key, Body=jpg_data, ContentType='image/jpeg')
    print(f"  {title}: ✅ fixed ({len(jpg_data)//1024}KB)")
    fixed += 1

print(f"\n{'='*50}")
print(f"  Fixed: {fixed} | Already OK: {already_ok} | Failed: {failed}")
print(f"{'='*50}")
