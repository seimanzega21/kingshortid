#!/usr/bin/env python3
"""
VIDRAMA → R2 PARALLEL SCRAPER (Direct MP4 Upload)
==================================================
Parallelized version: 4 drama workers, each processing episodes serially.
Skips dramas already in R2. Retries downloads with fresh proxy URLs.

Usage:
  python vidrama_parallel.py                   # Scrape 300 new dramas
  python vidrama_parallel.py --limit 10        # Scrape 10 new dramas
  python vidrama_parallel.py --workers 6       # Use 6 parallel workers
"""
import requests, json, time, os, re, sys, tempfile, shutil
from pathlib import Path
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

load_dotenv()

# R2 config
R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET = os.getenv("R2_BUCKET_NAME")
R2_PUBLIC = "https://stream.shortlovers.id"
API_URL = "https://vidrama.asia/api/melolo"
BACKEND_URL = "http://localhost:3001/api"

# Temp dir
TEMP_DIR = Path(tempfile.gettempdir()) / "vidrama_parallel"
TEMP_DIR.mkdir(exist_ok=True)

# Timeouts
API_TIMEOUT = 15
DOWNLOAD_TIMEOUT = 90

# Thread-local S3 clients
_local = threading.local()
_print_lock = threading.Lock()

# Global stats
stats_lock = threading.Lock()
stats = {"ok": 0, "fail": 0, "eps": 0, "skipped": 0}


def tprint(msg):
    with _print_lock:
        print(msg, flush=True)


def get_s3():
    if not hasattr(_local, "s3"):
        import boto3
        _local.s3 = boto3.client("s3",
            endpoint_url=R2_ENDPOINT,
            aws_access_key_id=R2_ACCESS_KEY,
            aws_secret_access_key=R2_SECRET_KEY,
        )
    return _local.s3


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return re.sub(r'-+', '-', text).strip('-')


# ─── R2 EXISTENCE CHECK ─────────────────────────────────────

def r2_key_exists(key):
    """Check if a key exists in R2."""
    try:
        get_s3().head_object(Bucket=R2_BUCKET, Key=key)
        return True
    except:
        return False


def get_r2_existing_slugs():
    """List all existing drama slugs in R2 melolo/ prefix."""
    tprint("  Scanning R2 for existing dramas...")
    existing = set()
    try:
        s3 = get_s3()
        paginator = s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=R2_BUCKET, Prefix="melolo/", Delimiter="/"):
            for prefix in page.get("CommonPrefixes", []):
                slug = prefix["Prefix"].replace("melolo/", "").rstrip("/")
                if slug:
                    existing.add(slug)
    except Exception as e:
        tprint(f"  ⚠️ R2 scan error: {e}")
    tprint(f"  Found {len(existing)} existing dramas in R2")
    return existing


# ─── DISCOVERY ───────────────────────────────────────────────

def load_discovered_dramas():
    """Load from saved discovery file or run discovery."""
    cache = Path("vidrama_all_dramas.json")
    if cache.exists():
        with open(cache, "r", encoding="utf-8") as f:
            dramas = json.load(f)
        if len(dramas) > 100:
            tprint(f"  Loaded {len(dramas)} dramas from cache")
            return dramas

    tprint("  Running fresh discovery...")
    return search_all_dramas()


def search_all_dramas():
    """Discover all dramas from vidrama search API."""
    all_dramas = {}
    keywords = ["a", "e", "i", "o", "u", "s", "k", "p", "d", "m",
                "b", "c", "r", "n", "t", "l", "g", "h", "j", "w"]

    for kw in keywords:
        offset = 0
        while True:
            try:
                r = requests.get(
                    f"{API_URL}?action=search&keyword={kw}&limit=50&offset={offset}",
                    timeout=API_TIMEOUT
                )
                if r.status_code != 200:
                    break
                items = r.json().get("data", [])
                if not items:
                    break
                for item in items:
                    did = item.get("id", "")
                    if did and did not in all_dramas:
                        all_dramas[did] = item
                if len(items) < 50:
                    break
                offset += 50
                time.sleep(0.5)
            except:
                break
        tprint(f"  '{kw}' → {len(all_dramas)} unique")
        time.sleep(0.3)

    # Trending
    try:
        r = requests.get(f"{API_URL}?action=all-trending&limit=100", timeout=API_TIMEOUT)
        if r.status_code == 200:
            for item in r.json().get("data", []):
                did = item.get("id", "")
                if did and did not in all_dramas:
                    all_dramas[did] = item
    except:
        pass

    dramas = list(all_dramas.values())
    with open("vidrama_all_dramas.json", "w", encoding="utf-8") as f:
        json.dump(dramas, f, indent=2, ensure_ascii=False)
    return dramas




# ─── DOWNLOAD + UPLOAD ──────────────────────────────────────

def download_mp4(proxy_url, output_path, tag=""):
    full_url = f"https://vidrama.asia{proxy_url}" if proxy_url.startswith("/") else proxy_url
    try:
        resp = requests.get(full_url, timeout=DOWNLOAD_TIMEOUT, stream=True)
        resp.raise_for_status()
        total = 0
        with open(output_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
                total += len(chunk)
        return total > 1000
    except requests.exceptions.Timeout:
        tprint(f"      {tag} ⏳ Download timeout (>{DOWNLOAD_TIMEOUT}s)")
        return False
    except:
        return False


def upload_to_r2(file_path, r2_key):
    try:
        ct = "video/mp4" if r2_key.endswith(".mp4") else "image/webp"
        get_s3().upload_file(str(file_path), R2_BUCKET, r2_key,
            ExtraArgs={"ContentType": ct})
        return True
    except Exception as e:
        tprint(f"        R2 error: {str(e)[:60]}")
        return False


def upload_cover_to_r2(urls, r2_key):
    """Try multiple cover URLs until one works."""
    if isinstance(urls, str):
        urls = [urls]
    for url in urls:
        if not url:
            continue
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            if len(resp.content) < 100:
                continue
            get_s3().put_object(Bucket=R2_BUCKET, Key=r2_key,
                Body=resp.content,
                ContentType=resp.headers.get("content-type", "image/webp"))
            return True
        except:
            continue
    return False


# ─── GENRE INFERENCE ─────────────────────────────────────────

GENRE_KEYWORDS = {
    'Romantis': ['cinta', 'nikah', 'menikah', 'istri', 'suami', 'manja', 'dimanja', 'romansa', 'kekasih', 'pacar'],
    'Aksi': ['pertarungan', 'pedang', 'penguasa', 'penakluk', 'senjata', 'lawan', 'perang', 'bangkit'],
    'Drama Keluarga': ['ibu', 'mertua', 'anak', 'keluarga', 'ayah', 'kakak', 'saudara', 'tiri'],
    'Misteri': ['rahasia', 'misteri', 'tersembunyi', 'dusta', 'fitnah'],
    'Fantasi': ['portal', 'dunia lain', 'dinasti', 'dewi', 'dewa', 'legenda', 'lahir kembali', 'bertapa', 'sakti', 'ajaib'],
    'Balas Dendam': ['balas dendam', 'menyesal', 'penyesalan', 'pengkhianatan'],
    'Bisnis': ['bos', 'ceo', 'kaya', 'harta', 'saham', 'kantor', 'pengacara', 'investor', 'pewaris', 'presdir'],
    'Kehidupan': ['desa', 'kampung', 'petani', 'tabib', 'dokter', 'guru'],
}

def infer_genres(title):
    """Infer genres from Indonesian drama title keywords."""
    lower = title.lower()
    genres = set()
    for genre, keywords in GENRE_KEYWORDS.items():
        for kw in keywords:
            if kw in lower:
                genres.add(genre)
                break
    return list(genres) if genres else ['Drama']


# ─── VALIDATION GATE ────────────────────────────────────────

def validate_before_register(slug, uploaded_eps, drama_info, detail_data=None):
    """Validate data quality BEFORE registering in DB. Returns (ok, issues)."""
    issues = []

    # 1. Check cover exists in R2
    try:
        get_s3().head_object(Bucket=R2_BUCKET, Key=f"melolo/{slug}/cover.webp")
    except:
        issues.append("NO_COVER_IN_R2")

    # 2. Check episode 1 exists
    ep_numbers = sorted([e["number"] for e in uploaded_eps])
    if not ep_numbers or ep_numbers[0] != 1:
        issues.append("MISSING_EP1")

    # 3. Check for large episode gaps
    if len(ep_numbers) > 1:
        gaps = 0
        for i in range(1, len(ep_numbers)):
            if ep_numbers[i] != ep_numbers[i-1] + 1:
                gaps += 1
        if gaps > len(ep_numbers) * 0.1 and gaps > 3:
            issues.append(f"TOO_MANY_GAPS({gaps})")

    # 4. Check description is reasonable
    desc = drama_info.get("description", "") or drama_info.get("desc", "")
    if detail_data:
        desc = detail_data.get("description", desc) or desc
    if not desc or len(desc.strip()) < 10 or desc.strip() == drama_info.get("title", ""):
        issues.append("WEAK_DESC")

    return (len(issues) == 0, issues)


# ─── BACKEND ────────────────────────────────────────────────

def register_drama(drama_info, slug, uploaded_eps, detail_data=None, total_expected=0):
    """Register drama + episodes in backend. Only called when ALL episodes are complete."""
    try:
        # Build genre list with inference fallback
        genres = []
        if detail_data and detail_data.get("genres"):
            genres = detail_data["genres"]
        elif drama_info.get("genres"):
            genres = drama_info["genres"]
        elif drama_info.get("tags"):
            genres = drama_info["tags"]
        if not genres:
            genres = infer_genres(drama_info["title"])

        # Build description with better fallback
        desc = ""
        if detail_data:
            desc = detail_data.get("description", "") or ""
        if not desc.strip():
            desc = drama_info.get("description", "") or drama_info.get("desc", "") or ""
        if not desc.strip() or desc.strip() == drama_info["title"]:
            desc = f"{drama_info['title']} — Drama seru dari China dengan subtitle Indonesia."

        payload = {
            "title": drama_info["title"],
            "description": desc.strip(),
            "cover": f"{R2_PUBLIC}/melolo/{slug}/cover.webp",
            "genres": genres,
            "status": "completed",
            "country": "China",
            "language": "Indonesia",
        }
        r = requests.post(f"{BACKEND_URL}/dramas", json=payload, timeout=15)
        if r.status_code not in [200, 201]:
            tprint(f"    ⚠️ Drama API error: {r.status_code} {r.text[:120]}")
            return False

        drama_id = r.json().get("id")
        if not drama_id:
            tprint(f"    ⚠️ No drama ID in response")
            return False

        # Register all episodes
        fail_count = 0
        for ep in uploaded_eps:
            ep_payload = {
                "dramaId": drama_id,
                "episodeNumber": ep["number"],
                "title": f"Episode {ep['number']}",
                "videoUrl": ep["videoUrl"],
                "duration": ep.get("duration", 0),
            }
            try:
                er = requests.post(f"{BACKEND_URL}/episodes", json=ep_payload, timeout=10)
                if er.status_code not in [200, 201]:
                    fail_count += 1
            except:
                fail_count += 1

        if fail_count > 0:
            tprint(f"    ⚠️ {fail_count} episode registrations failed")
        return True
    except Exception as e:
        tprint(f"    ⚠️ Backend error: {e}")
        return False


# ─── PROCESS ONE DRAMA ──────────────────────────────────────

def process_drama(drama, slug, index, total):
    """Process a single drama: detail → download → transcode → R2 → backend."""
    drama_id = drama["id"]
    title = drama["title"]
    tag = f"[{index}/{total}]"

    tprint(f"\n{'─' * 60}")
    tprint(f"  {tag} {title}")
    tprint(f"  Slug: {slug}")

    # Get episode list from detail API
    detail = None
    for attempt in range(3):
        try:
            r = requests.get(f"{API_URL}?action=detail&id={drama_id}", timeout=API_TIMEOUT)
            if r.status_code == 200:
                detail = r.json().get("data", {})
                break
            time.sleep(2)
        except:
            time.sleep(2)

    if not detail:
        tprint(f"  {tag} ❌ Detail API failed after 3 retries")
        with stats_lock:
            stats["fail"] += 1
        return

    episodes = detail.get("episodes", [])
    if not episodes:
        tprint(f"  {tag} ❌ No episodes found")
        with stats_lock:
            stats["fail"] += 1
        return

    total_eps = len(episodes)
    tprint(f"  {tag} Episodes: {total_eps}")

    # Upload cover — try original URLs first (wsrv.nl proxy URLs expire)
    cover_urls = [
        drama.get("originalImage"),
        drama.get("originalPoster"),
        detail.get("originalPoster"),
        detail.get("poster"),
        drama.get("image"),
        drama.get("poster"),
    ]
    cover_urls = [u for u in cover_urls if u]
    if cover_urls:
        ok = upload_cover_to_r2(cover_urls, f"melolo/{slug}/cover.webp")
        tprint(f"  {tag} Cover: {'✅' if ok else '❌'}")
    else:
        tprint(f"  {tag} Cover: ❌ No URL available")

    # Save metadata to R2
    metadata = {
        "title": title,
        "description": drama.get("description", "") or drama.get("desc", ""),
        "genres": detail.get("genres", drama.get("genres", drama.get("tags", []))),
        "totalEpisodes": total_eps,
        "provider": "melolo",
        "vidramaId": drama_id,
    }
    try:
        meta_bytes = json.dumps(metadata, ensure_ascii=False, indent=2).encode("utf-8")
        get_s3().put_object(
            Bucket=R2_BUCKET,
            Key=f"melolo/{slug}/metadata.json",
            Body=meta_bytes,
            ContentType="application/json"
        )
    except:
        pass

    # Process episodes
    uploaded = []
    drama_temp = TEMP_DIR / slug
    drama_temp.mkdir(exist_ok=True)

    for ep in episodes:
        ep_num = ep.get("episodeNumber", 0)
        if ep_num == 0:
            continue

        r2_key = f"melolo/{slug}/ep{ep_num:03d}.mp4"

        # Skip if already uploaded
        if r2_key_exists(r2_key):
            tprint(f"    {tag} Ep {ep_num:3}/{total_eps}: ⏭️ already in R2")
            uploaded.append({
                "number": ep_num,
                "videoUrl": f"{R2_PUBLIC}/{r2_key}",
                "duration": ep.get("duration", 0),
            })
            continue

        # Retry up to 3 times: each retry fetches a FRESH proxy URL
        raw_path = drama_temp / f"ep{ep_num:03d}.mp4"
        success = False

        for attempt in range(3):
            # Get fresh stream URL each attempt
            try:
                sr = requests.get(
                    f"{API_URL}?action=stream&id={drama_id}&episode={ep_num}",
                    timeout=API_TIMEOUT
                )
                if sr.status_code != 200:
                    time.sleep(2 * (attempt + 1))
                    continue
                stream_data = sr.json().get("data", {})
            except:
                time.sleep(2 * (attempt + 1))
                continue

            proxy_url = stream_data.get("proxyUrl", "")
            if not proxy_url:
                time.sleep(2 * (attempt + 1))
                continue

            # Download raw MP4 (no FFmpeg)
            if download_mp4(proxy_url, raw_path, tag):
                success = True
                break

            # Clean up failed download before retry
            raw_path.unlink(missing_ok=True)
            if attempt < 2:
                tprint(f"    {tag} Ep {ep_num:3}/{total_eps}: 🔄 Retry {attempt + 2}/3")
            time.sleep(2 * (attempt + 1))

        if not success:
            tprint(f"    {tag} Ep {ep_num:3}/{total_eps}: ❌ Failed after 3 attempts")
            raw_path.unlink(missing_ok=True)
            continue

        file_mb = raw_path.stat().st_size / 1024 / 1024

        # Upload directly to R2 (no FFmpeg)
        if upload_to_r2(raw_path, r2_key):
            tprint(f"    {tag} Ep {ep_num:3}/{total_eps}: ✅ {file_mb:.1f}MB")
            uploaded.append({
                "number": ep_num,
                "videoUrl": f"{R2_PUBLIC}/{r2_key}",
                "duration": ep.get("duration", 0),
            })
        else:
            tprint(f"    {tag} Ep {ep_num:3}/{total_eps}: ❌ Upload failed")

        # Cleanup with retry for WinError 32 (file still locked)
        for _ in range(3):
            try:
                raw_path.unlink(missing_ok=True)
                break
            except OSError:
                time.sleep(0.5)
        time.sleep(0.3)

    # Cleanup temp dir with retry
    for _ in range(3):
        try:
            shutil.rmtree(drama_temp, ignore_errors=False)
            break
        except OSError:
            time.sleep(1)
    shutil.rmtree(drama_temp, ignore_errors=True)  # final fallback

    # Only register in backend if ALL episodes uploaded (complete drama)
    if uploaded and len(uploaded) == total_eps:
        # VALIDATION GATE: check data quality before DB registration
        valid, issues = validate_before_register(slug, uploaded, drama, detail)
        if not valid:
            tprint(f"  {tag} ⚠️ {title}: VALIDATION FAILED — {', '.join(issues)} (skipping DB, R2 data kept)")
            with stats_lock:
                stats["eps"] += len(uploaded)
        elif register_drama(drama, slug, uploaded, detail, total_eps):
            tprint(f"  {tag} ✅ {title}: {len(uploaded)}/{total_eps} episodes → DB registered")
            with stats_lock:
                stats["ok"] += 1
                stats["eps"] += len(uploaded)
        else:
            tprint(f"  {tag} ⚠️ {title}: R2 complete but DB registration failed")
            with stats_lock:
                stats["fail"] += 1
    elif uploaded:
        tprint(f"  {tag} ⏳ {title}: {len(uploaded)}/{total_eps} episodes in R2 (incomplete, skipping DB)")
        with stats_lock:
            stats["eps"] += len(uploaded)
    else:
        tprint(f"  {tag} ❌ {title}: no episodes uploaded")
        with stats_lock:
            stats["fail"] += 1


# ─── MAIN ────────────────────────────────────────────────────

def main():
    limit = 300
    workers = 4

    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        if idx + 1 < len(sys.argv):
            limit = int(sys.argv[idx + 1])

    if "--workers" in sys.argv:
        idx = sys.argv.index("--workers")
        if idx + 1 < len(sys.argv):
            workers = int(sys.argv[idx + 1])

    print("=" * 70)
    print("  VIDRAMA → R2 PARALLEL SCRAPER")
    print(f"  Target: {limit} dramas | Workers: {workers}")
    print("=" * 70)

    # Load dramas
    dramas = load_discovered_dramas()
    if not dramas:
        print("  ❌ No dramas found. Run vidrama_to_r2.py first for discovery.")
        return

    # Check R2 for already-uploaded dramas
    existing_slugs = get_r2_existing_slugs()

    # Filter new dramas
    new_dramas = []
    for d in dramas:
        slug = slugify(d["title"])
        if slug not in existing_slugs:
            new_dramas.append((d, slug))

    print(f"\n  Total discovered: {len(dramas)}")
    print(f"  Already in R2: {len(existing_slugs)}")
    print(f"  New to scrape: {len(new_dramas)}")

    if not new_dramas:
        print("  Nothing new to scrape!")
        return

    # Limit
    batch = new_dramas[:limit]
    print(f"  Batch size: {len(batch)}")
    print(f"\n  Starting {workers} parallel workers...\n")

    # Parallel execution
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {}
        for i, (drama, slug) in enumerate(batch, 1):
            f = executor.submit(process_drama, drama, slug, i, len(batch))
            futures[f] = drama["title"]

        for f in as_completed(futures):
            title = futures[f]
            try:
                f.result()
            except Exception as e:
                tprint(f"  ❌ Exception processing '{title}': {e}")
                with stats_lock:
                    stats["fail"] += 1

    print(f"\n{'=' * 70}")
    print(f"  DONE!")
    print(f"  Success: {stats['ok']} dramas, {stats['eps']} episodes")
    print(f"  Failed: {stats['fail']}")
    print(f"  Skipped (already in R2): {len(existing_slugs)}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
