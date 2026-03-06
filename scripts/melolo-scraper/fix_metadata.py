import requests, json, time, os, re
import boto3
from dotenv import load_dotenv
load_dotenv()

API_URL = "https://vidrama.asia/api/melolo"
BACKEND_URL = "http://localhost:3001/api"
R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET = os.getenv("R2_BUCKET_NAME")
R2_PUBLIC = "https://stream.shortlovers.id"

s3 = boto3.client("s3", endpoint_url=R2_ENDPOINT,
    aws_access_key_id=R2_ACCESS_KEY, aws_secret_access_key=R2_SECRET_KEY)

# The two dramas we need to register
DRAMAS_TO_FIX = [
    {"search": "Romansa Setelah Pernikahan", "slug": "romansa-setelah-pernikahan", "eps_on_r2": 26},
    {"search": "Dimanja Habis", "slug": "dimanja-habis-habisan-oleh-bos", "eps_on_r2": 38},
]

def find_drama_on_vidrama(search_term):
    """Find drama on Vidrama API."""
    r = requests.get(f"{API_URL}?action=search&keyword={search_term}&limit=10", timeout=15)
    if r.status_code != 200:
        return None
    for d in r.json().get("data", []):
        if search_term.lower() in d["title"].lower():
            return d
    return None

def get_drama_detail(drama_id):
    """Get full detail from Vidrama."""
    r = requests.get(f"{API_URL}?action=detail&id={drama_id}", timeout=15)
    if r.status_code == 200:
        return r.json().get("data", {})
    return {}

def upload_cover_direct(image_url, r2_key):
    """Download cover directly and upload to R2. Try multiple URL sources."""
    urls_to_try = [image_url]
    
    # If it's a wsrv.nl proxy URL, extract the original URL
    if "wsrv.nl" in image_url or "wsrv" in image_url:
        # Try to extract original URL from query params
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(image_url)
        qs = parse_qs(parsed.query)
        if "url" in qs:
            urls_to_try.insert(0, qs["url"][0])
    
    for url in urls_to_try:
        try:
            print(f"    Trying cover: {url[:80]}...")
            resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            if len(resp.content) < 100:
                continue
            ct = resp.headers.get("content-type", "image/jpeg")
            s3.put_object(Bucket=R2_BUCKET, Key=r2_key, Body=resp.content, ContentType=ct)
            print(f"    ✅ Cover uploaded ({len(resp.content)/1024:.0f}KB)")
            return True
        except Exception as e:
            print(f"    ❌ Failed: {str(e)[:60]}")
    return False

def register_in_backend(title, description, slug, cover_key, genres, total_eps, eps_on_r2):
    """Register drama + episodes in backend."""
    cover_url = f"{R2_PUBLIC}/{cover_key}" if cover_key else ""
    
    payload = {
        "title": title,
        "description": description,
        "coverUrl": cover_url,
        "provider": "melolo",
        "totalEpisodes": total_eps,
        "genres": genres if isinstance(genres, list) else [],
        "isActive": True,
    }
    
    print(f"  Registering drama: {title}")
    print(f"    desc: {description[:80]}..." if description else "    desc: (none)")
    print(f"    genres: {genres}")
    print(f"    cover: {cover_url}")
    
    r = requests.post(f"{BACKEND_URL}/dramas", json=payload, timeout=10)
    if r.status_code not in [200, 201]:
        print(f"    ⚠️ Drama API error: {r.status_code} {r.text[:80]}")
        return False
    
    drama_id = r.json().get("id")
    print(f"    Drama ID: {drama_id}")
    
    # Register episodes that exist on R2
    registered = 0
    for ep_num in range(1, eps_on_r2 + 1):
        video_url = f"{R2_PUBLIC}/melolo/{slug}/ep{ep_num:03d}.mp4"
        r = requests.post(f"{BACKEND_URL}/episodes", json={
            "dramaId": drama_id,
            "episodeNumber": ep_num,
            "videoUrl": video_url,
            "duration": 0,
        }, timeout=10)
        if r.status_code in [200, 201]:
            registered += 1
    
    print(f"    ✅ Registered {registered}/{eps_on_r2} episodes")
    return True

# ─── MAIN ────────────────────────────────────────────────────

for item in DRAMAS_TO_FIX:
    print(f"\n{'='*60}")
    print(f"  {item['search']}")
    print(f"  Slug: {item['slug']}")
    print(f"  Episodes on R2: {item['eps_on_r2']}")
    print(f"{'='*60}")
    
    # Find on Vidrama
    drama = find_drama_on_vidrama(item["search"])
    if not drama:
        print("  ❌ Not found on Vidrama!")
        continue
    
    print(f"  Found: {drama['title']} (id={drama['id']})")
    
    # Get detail
    detail = get_drama_detail(drama["id"])
    title = drama["title"]
    description = detail.get("description", detail.get("desc", drama.get("description", "")))
    genres = detail.get("genres", drama.get("genres", []))
    total_eps = len(detail.get("episodes", []))
    
    print(f"  Total episodes on Vidrama: {total_eps}")
    
    # Upload cover
    cover_url = drama.get("image") or drama.get("poster", "")
    cover_key = f"melolo/{item['slug']}/cover.jpg"
    
    if cover_url:
        ok = upload_cover_direct(cover_url, cover_key)
        if not ok:
            # Try poster from detail
            alt_cover = detail.get("image", detail.get("poster", ""))
            if alt_cover and alt_cover != cover_url:
                ok = upload_cover_direct(alt_cover, cover_key)
    
    # Register in backend
    register_in_backend(title, description, item["slug"], cover_key, genres, total_eps, item["eps_on_r2"])
    
    time.sleep(1)

print("\n✅ Done fixing metadata and covers!")
