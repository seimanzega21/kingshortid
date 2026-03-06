#!/usr/bin/env python3
"""Fix the remaining 3 broken covers by downloading from wsrv.nl proxy directly."""
import requests, os, sys
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "melolo-scraper", ".env"))

R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET = os.getenv("R2_BUCKET_NAME")
R2_PUBLIC = "https://stream.shortlovers.id"
BACKEND_API = "https://api.shortlovers.id/api"

# 3 remaining broken dramas with their wsrv.nl cover URLs
REMAINING = [
    {
        "title": "Nikah Instan Cinta Tak Terduga",
        "db_title": "Nikah Instan Cinta Tak Terduga",
        "slug": "nikah-instan-cinta-tak-terduga",
        "cover_url": "https://wsrv.nl/?url=https%3A%2F%2Fp16-novel-sign-sg.fizzopic.org%2Fnovel-images-sg%2F5dc19f3c495bb721a337dbc4b42bdecb%7Etplv-resize%3A570%3A810.heic%3Frk3s%3D95ec04ee%26x-expires%3D1773273706%26x-signature%3DMYjpR278buTm57VAqoGoV0%252FNzKs%253D&output=webp&q=60&il=&af=&w=300",
    },
    {
        "title": "Diusir Dari Rumah, Saya Mewarisi Miliaran",
        "db_title": "Diusir Dari Rumah Saya Mewarisi Miliaran",
        "slug": "diusir-dari-rumah-saya-mewarisi-miliaran",
        "cover_url": "https://wsrv.nl/?url=https%3A%2F%2Fp19-novel-sign-sg.fizzopic.org%2Fnovel-images-sg%2F43bb2c82bf7d2ed8482485659921974e%7Etplv-resize%3A570%3A810.heic%3Frk3s%3D95ec04ee%26x-expires%3D1773273706%26x-signature%3DeX%252BhHlt%252FQV0wYLpH6AEwPetQBXY%253D&output=webp&q=60&il=&af=&w=300",
    },
    {
        "title": "Dimanja Habis-habisan oleh Bos",
        "db_title": "Dimanja Habis Habisan Oleh Bos",
        "slug": "dimanja-habis-habisan-oleh-bos",
        "cover_url": "https://wsrv.nl/?url=https%3A%2F%2Fp16-novel-sign-sg.fizzopic.org%2Fnovel-images-sg%2F17d495d216ef9621d58e65d7edff636a%7Etplv-resize%3A570%3A810.heic%3Frk3s%3D95ec04ee%26x-expires%3D1773273706%26x-signature%3D1bq9qrNGpcdvBHxeLu3d6990nro%253D&output=webp&q=60&il=&af=&w=300",
    },
]

import boto3
s3 = boto3.client("s3",
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY,
)

for drama in REMAINING:
    print(f"\n[{drama['title']}]")
    
    # Download cover via wsrv.nl (it acts as image proxy + converter)
    print(f"  Downloading from wsrv.nl...", end="", flush=True)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "image/*,*/*",
    }
    try:
        r = requests.get(drama["cover_url"], timeout=20, headers=headers)
        r.raise_for_status()
        img = r.content
        ct = r.headers.get("content-type", "image/webp")
        print(f" ✅ ({len(img)//1024}KB, {ct})")
    except Exception as e:
        print(f" ❌ {e}")
        continue
    
    if len(img) < 100:
        print(f"  ❌ Image too small ({len(img)} bytes)")
        continue
    
    # Upload to R2
    r2_key = f"melolo/{drama['slug']}/cover.webp"
    print(f"  Uploading to R2: {r2_key}...", end="", flush=True)
    try:
        s3.put_object(Bucket=R2_BUCKET, Key=r2_key, Body=img, ContentType=ct)
        print(f" ✅")
    except Exception as e:
        print(f" ❌ {e}")
        continue
    
    # Update DB cover URL via API POST (upsert)
    new_cover = f"{R2_PUBLIC}/melolo/{drama['slug']}/cover.webp"
    print(f"  Updating DB: {new_cover}...", end="", flush=True)
    try:
        r = requests.post(f"{BACKEND_API}/dramas", json={
            "title": drama["db_title"],
            "cover": new_cover,
        }, timeout=10)
        if r.status_code in [200, 201]:
            print(f" ✅")
        else:
            print(f" ❌ API {r.status_code}: {r.text[:80]}")
    except Exception as e:
        print(f" ❌ {e}")

print("\n✅ Done!")
