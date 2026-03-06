#!/usr/bin/env python3
"""
Fix broken drama covers by:
1. Searching Vidrama API for the drama
2. Downloading the cover image
3. Uploading to R2 at the correct path
4. Updating the backend DB cover URL via API POST (upsert)

Usage:
  python fix_covers.py           # Dry run - just show what would be fixed
  python fix_covers.py --fix     # Actually fix the covers
"""
import requests, os, sys, re, time
from dotenv import load_dotenv

# Load .env from melolo-scraper directory
load_dotenv(os.path.join(os.path.dirname(__file__), "melolo-scraper", ".env"))

R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET = os.getenv("R2_BUCKET_NAME")
R2_PUBLIC = "https://stream.shortlovers.id"

VIDRAMA_API = "https://vidrama.asia/api/melolo"
BACKEND_API = "https://api.shortlovers.id/api"

# 8 broken dramas
BROKEN_DRAMAS = [
    {"title": "Tangi Penyesalan Bos Cantik", "id": "cmlkd3jl408sr13mdwb3z00xe", "slug": "tangi-penyesalan-bos-cantik"},
    {"title": "Tangkap Harta Karun Di Kampung", "id": "cmlkd3jny08vk13mde1sm5xpe", "slug": "tangkap-harta-karun-di-kampung"},
    {"title": "Sadar Akan Realita", "id": "cmlkd335g082m13md4l8sy2gk", "slug": "sadar-akan-realita"},
    {"title": "Salah Meja Nikah Dengan Dokter", "id": "cmlkd33al084b13mddoez6bxe", "slug": "salah-meja-nikah-dengan-dokter"},
    {"title": "Nikah Instan Cinta Tak Terduga", "id": "cmlkd2nkk06ep13mdctgduhwg", "slug": "nikah-instan-cinta-tak-terduga"},
    {"title": "Harta Tahta Dan Ketulusan", "id": "cmlkd1mja039a13mdziuyhnn0", "slug": "harta-tahta-dan-ketulusan"},
    {"title": "Diusir Dari Rumah Saya Mewarisi Miliaran", "id": "cmlkd1a9z02np13md4skw9u6z", "slug": "diusir-dari-rumah-saya-mewarisi-miliaran"},
    {"title": "Dimanja Habis Habisan Oleh Bos", "id": "cmlkd18oz026w13md09zpb4w4", "slug": "dimanja-habis-habisan-oleh-bos"},
]

_s3 = None
def get_s3():
    global _s3
    if _s3 is None:
        import boto3
        _s3 = boto3.client("s3",
            endpoint_url=R2_ENDPOINT,
            aws_access_key_id=R2_ACCESS_KEY,
            aws_secret_access_key=R2_SECRET_KEY,
        )
    return _s3


def normalize(s):
    return re.sub(r'[^a-z0-9\s]', '', s.lower().strip())

def search_vidrama(title):
    """Search Vidrama API for a drama by title keywords."""
    target = normalize(title)
    target_words = set(target.split())
    
    # Try multiple keyword searches  
    keywords_to_try = [
        title.split()[0].lower(),  # first word
        " ".join(title.split()[:2]).lower(),  # first 2 words
        " ".join(title.split()[:3]).lower(),  # first 3 words
    ]
    
    all_candidates = {}
    
    for kw in keywords_to_try:
        for offset in [0, 50]:
            try:
                r = requests.get(
                    f"{VIDRAMA_API}?action=search&keyword={kw}&limit=50&offset={offset}",
                    timeout=15
                )
                if r.status_code == 200:
                    items = r.json().get("data", [])
                    for item in items:
                        did = item.get("id", "")
                        if did and did not in all_candidates:
                            all_candidates[did] = item
                time.sleep(0.3)
            except Exception as e:
                print(f"\n    Search error '{kw}': {e}")
                time.sleep(1)
    
    if not all_candidates:
        return None
    
    # Score each candidate by word overlap
    best_match = None
    best_score = 0
    
    for item in all_candidates.values():
        item_title = normalize(item.get("title", ""))
        item_words = set(item_title.split())
        
        # Exact match
        if item_title == target:
            return item
        
        # Word overlap score (Jaccard-like)
        overlap = len(target_words & item_words)
        score = overlap / max(len(target_words | item_words), 1)
        
        if score > best_score:
            best_score = score
            best_match = item
    
    # Require at least 60% word overlap
    if best_score >= 0.6:
        return best_match
    
    return None


def download_cover(url):
    """Download cover image bytes. Handles wsrv.nl proxy URLs."""
    from urllib.parse import urlparse, parse_qs, unquote
    
    # If it's a wsrv.nl proxy URL, extract the original image URL
    if "wsrv.nl" in url:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        original_url = params.get("url", [None])[0]
        if original_url:
            url = unquote(original_url)
    
    full_url = f"https://vidrama.asia{url}" if url.startswith("/") else url
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "image/*,*/*",
        "Referer": "https://vidrama.asia/",
    }
    
    try:
        r = requests.get(full_url, timeout=15, headers=headers)
        r.raise_for_status()
        if len(r.content) > 100:
            ct = r.headers.get("content-type", "image/webp")
            return r.content, ct
    except Exception as e:
        # Fallback: try wsrv.nl with headers
        try:
            r2 = requests.get(f"https://wsrv.nl/?url={full_url}&output=webp&w=400", timeout=15, headers=headers)
            r2.raise_for_status()
            if len(r2.content) > 100:
                return r2.content, "image/webp"
        except:
            pass
        print(f" ❌ Download error: {e}")
    return None, None


def upload_cover_r2(image_bytes, content_type, r2_key):
    """Upload cover image to R2."""
    try:
        s3 = get_s3()
        s3.put_object(
            Bucket=R2_BUCKET,
            Key=r2_key,
            Body=image_bytes,
            ContentType=content_type,
        )
        return True
    except Exception as e:
        print(f"    R2 upload error: {e}")
        return False


def update_cover_in_db(title, cover_url):
    """Update drama cover URL in backend via POST (upsert)."""
    try:
        r = requests.post(f"{BACKEND_API}/dramas", json={
            "title": title,
            "cover": cover_url,
        }, timeout=10)
        if r.status_code in [200, 201]:
            return True
        print(f"    API error: {r.status_code} {r.text[:100]}")
    except Exception as e:
        print(f"    API error: {e}")
    return False


def main():
    do_fix = "--fix" in sys.argv
    
    print("=" * 60)
    print(f"  BROKEN COVER FIXER ({'FIX MODE' if do_fix else 'DRY RUN'})")
    print("=" * 60)
    
    stats = {"found": 0, "fixed": 0, "failed": 0}
    
    for i, drama in enumerate(BROKEN_DRAMAS, 1):
        print(f"\n[{i}/8] {drama['title']}")
        print(f"  Slug: {drama['slug']}")
        
        # Search on Vidrama
        print(f"  Searching vidrama...", end="", flush=True)
        result = search_vidrama(drama["title"])
        
        if not result:
            print(f" ❌ NOT FOUND on Vidrama")
            stats["failed"] += 1
            continue
        
        cover_url = result.get("image") or result.get("poster", "")
        print(f" ✅ Found!")
        print(f"  Vidrama cover: {cover_url[:80]}")
        stats["found"] += 1
        
        if not do_fix:
            print(f"  [DRY RUN] Would download and upload to R2")
            continue
        
        # Download cover
        print(f"  Downloading cover...", end="", flush=True)
        img_bytes, content_type = download_cover(cover_url)
        if not img_bytes:
            print(f" ❌ Download failed")
            stats["failed"] += 1
            continue
        print(f" ✅ ({len(img_bytes)//1024}KB, {content_type})")
        
        # Upload to R2
        r2_key = f"melolo/{drama['slug']}/cover.webp"
        print(f"  Uploading to R2: {r2_key}...", end="", flush=True)
        if not upload_cover_r2(img_bytes, content_type, r2_key):
            stats["failed"] += 1
            continue
        print(f" ✅")
        
        # Update DB
        new_cover_url = f"{R2_PUBLIC}/melolo/{drama['slug']}/cover.webp"
        print(f"  Updating DB cover URL...", end="", flush=True)
        if update_cover_in_db(drama["title"], new_cover_url):
            print(f" ✅")
            stats["fixed"] += 1
        else:
            print(f" ❌")
            stats["failed"] += 1
        
        time.sleep(0.5)
    
    print(f"\n{'=' * 60}")
    print(f"  RESULTS: Found {stats['found']}/8 | Fixed {stats['fixed']}/8 | Failed {stats['failed']}/8")
    print(f"{'=' * 60}")
    
    if not do_fix and stats["found"] > 0:
        print(f"\n  Run with --fix to actually fix the covers")


if __name__ == "__main__":
    main()
