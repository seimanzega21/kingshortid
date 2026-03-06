#!/usr/bin/env python3
"""Fix 5 additional broken covers by downloading from wsrv.nl via Vidrama search."""
import requests, os, re, time
from urllib.parse import unquote
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "melolo-scraper", ".env"))

R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET = os.getenv("R2_BUCKET_NAME")
R2_PUBLIC = "https://stream.shortlovers.id"
BACKEND_API = "https://api.shortlovers.id/api"
VIDRAMA_API = "https://vidrama.asia/api/melolo"

import boto3
s3 = boto3.client("s3",
    endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY,
)

DRAMAS = [
    {"db_title": "Sistem Harta Tersembunyi", "slug": "sistem-harta-tersembunyi", "search": "sistem harta tersembunyi"},
    {"db_title": "Aku Kaya Dari Giok", "slug": "aku-kaya-dari-giok", "search": "aku kaya dari giok"},
    {"db_title": "Pulang Kampung Bawa CEO", "slug": "pulang-kampung-bawa-ceo", "search": "pulang kampung bawa ceo"},
    {"db_title": "Bersinar Setelah Cerai", "slug": "bersinar-setelah-cerai", "search": "bersinar setelah cerai"},
    {"db_title": "Ahli Pengobatan Sakti", "slug": "ahli-pengobatan-sakti", "search": "ahli pengobatan sakti"},
]

def normalize(t):
    return re.sub(r'[^a-z0-9\s]', '', t.lower()).strip()

results = []

for drama in DRAMAS:
    print(f"\n[{drama['db_title']}]")
    
    # Search Vidrama
    print(f"  Searching Vidrama...", end="", flush=True)
    try:
        r = requests.get(f"{VIDRAMA_API}?action=search&keyword={drama['search']}&limit=10", timeout=15)
        data = r.json().get("data", [])
    except Exception as e:
        print(f" ❌ {e}")
        results.append((drama['db_title'], "SEARCH_FAIL"))
        continue
    
    # Find best match
    norm_title = normalize(drama['db_title'])
    match = None
    for d in data:
        if normalize(d.get("title","")) == norm_title:
            match = d
            break
    
    if not match:
        # Try partial match
        for d in data:
            if norm_title in normalize(d.get("title","")) or normalize(d.get("title","")) in norm_title:
                match = d
                break
    
    if not match and data:
        # Use first result as fallback if title words overlap significantly
        target_words = set(norm_title.split())
        for d in data:
            candidate_words = set(normalize(d.get("title","")).split())
            overlap = len(target_words & candidate_words) / max(len(target_words), 1)
            if overlap >= 0.6:
                match = d
                break
    
    if not match:
        print(f" ❌ Not found (got: {[d['title'] for d in data[:3]]})")
        results.append((drama['db_title'], "NOT_FOUND"))
        continue
    
    cover_url = match.get("image") or match.get("poster", "")
    print(f" ✅ Found: '{match['title']}'")
    
    if not cover_url:
        print(f"  ❌ No cover URL")
        results.append((drama['db_title'], "NO_COVER"))
        continue
    
    # Download cover from wsrv.nl
    print(f"  Downloading cover...", end="", flush=True)
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        r = requests.get(cover_url, timeout=20, headers=headers)
        r.raise_for_status()
        img = r.content
        ct = r.headers.get("content-type", "image/webp")
        print(f" ✅ ({len(img)//1024}KB, {ct})")
    except Exception as e:
        print(f" ❌ {e}")
        results.append((drama['db_title'], "DOWNLOAD_FAIL"))
        continue
    
    if len(img) < 100:
        print(f"  ❌ Image too small")
        results.append((drama['db_title'], "TOO_SMALL"))
        continue
    
    # Upload to R2
    r2_key = f"melolo/{drama['slug']}/cover.webp"
    print(f"  Uploading to R2: {r2_key}...", end="", flush=True)
    try:
        s3.put_object(Bucket=R2_BUCKET, Key=r2_key, Body=img, ContentType=ct)
        print(f" ✅")
    except Exception as e:
        print(f" ❌ {e}")
        results.append((drama['db_title'], "UPLOAD_FAIL"))
        continue
    
    # Update DB
    new_cover = f"{R2_PUBLIC}/melolo/{drama['slug']}/cover.webp"
    print(f"  Updating DB...", end="", flush=True)
    try:
        r = requests.post(f"{BACKEND_API}/dramas", json={
            "title": drama["db_title"],
            "cover": new_cover,
        }, timeout=10)
        if r.status_code in [200, 201]:
            print(f" ✅")
            results.append((drama['db_title'], "FIXED"))
        else:
            print(f" ❌ API {r.status_code}: {r.text[:80]}")
            results.append((drama['db_title'], "API_FAIL"))
    except Exception as e:
        print(f" ❌ {e}")
        results.append((drama['db_title'], "API_FAIL"))
    
    time.sleep(0.5)

print("\n" + "=" * 50)
print("RESULTS:")
for title, status in results:
    icon = "✅" if status == "FIXED" else "❌"
    print(f"  {icon} {title}: {status}")
print("=" * 50)
