#!/usr/bin/env python3
"""
MICRODRAMA -> R2 SCRAPER (Native Indonesian + Faststart + 8 Workers)
====================================================================
Scrapes dramas from vidrama.asia MicroDrama provider.
Uses lang=id API parameter for native Indonesian titles.
Downloads 720P MP4, applies faststart, uploads to R2.
8 parallel workers for fast downloading.

Usage:
  python microdrama_scraper.py                    # Scrape all
  python microdrama_scraper.py --limit 10         # Scrape 10 dramas
  python microdrama_scraper.py --workers 4        # Custom worker count
  python microdrama_scraper.py --register-only    # Register existing R2 data to DB
"""
import requests, json, time, os, re, sys, tempfile, shutil, subprocess, threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv()

# R2 config
R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET = os.getenv("R2_BUCKET_NAME")
R2_PUBLIC = "https://stream.shortlovers.id"

# API
API = "https://vidrama.asia/api/microdrama"
LANG = "id"
BACKEND_URL = os.getenv("BACKEND_URL", "https://api.shortlovers.id/api")

TEMP_DIR = Path(tempfile.gettempdir()) / "microdrama_scraper"
TEMP_DIR.mkdir(exist_ok=True)

# Thread-safe printing and stats
_print_lock = threading.Lock()
_stats_lock = threading.Lock()
stats = {"ok": 0, "fail": 0, "eps": 0, "ep_fail": 0, "skipped": 0}
_local = threading.local()

# Genre inference
GENRE_KEYWORDS = {
    'Romantis': ['cinta', 'nikah', 'menikah', 'istri', 'suami', 'manja', 'romansa', 'kekasih', 'pacar', 'pengantin', 'pernikahan', 'jatuh cinta'],
    'Aksi': ['pertarungan', 'pedang', 'penguasa', 'perang', 'kungfu', 'bertarung', 'prajurit'],
    'Drama Keluarga': ['ibu', 'mertua', 'anak', 'keluarga', 'ayah', 'mama', 'papa', 'adik', 'kakak'],
    'Misteri': ['rahasia', 'misteri', 'tersembunyi', 'identitas'],
    'Fantasi': ['naga', 'sihir', 'abadi', 'terlahir kembali', 'reinkarnasi', 'dewa'],
    'Balas Dendam': ['balas dendam', 'pengkhianatan', 'pembalasan', 'menyesal', 'dikhianati'],
    'Bisnis': ['ceo', 'miliarder', 'presdir', 'perusahaan', 'direktur', 'pewaris', 'kaya', 'pria kaya'],
}


def tprint(msg):
    with _print_lock:
        print(msg, flush=True)


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return re.sub(r'-+', '-', text).strip('-')


def infer_genres(title, desc=""):
    combined = f"{title} {desc}".lower()
    genres = set()
    for genre, keywords in GENRE_KEYWORDS.items():
        for kw in keywords:
            if kw in combined:
                genres.add(genre)
                break
    return list(genres) if genres else ['Drama']


def get_s3():
    if not hasattr(_local, "s3"):
        import boto3
        _local.s3 = boto3.client("s3",
            endpoint_url=R2_ENDPOINT,
            aws_access_key_id=R2_ACCESS_KEY,
            aws_secret_access_key=R2_SECRET_KEY,
        )
    return _local.s3


def r2_key_exists(s3, key):
    try:
        s3.head_object(Bucket=R2_BUCKET, Key=key)
        return True
    except:
        return False


def download_ep(ep, slug, total_eps, tag):
    """Download, faststart, upload one episode. Thread-safe."""
    s3 = get_s3()
    ep_idx = ep.get("index", 0)
    if ep_idx == 0:
        return None

    r2_key = f"microdrama/{slug}/ep{ep_idx:03d}.mp4"

    if r2_key_exists(s3, r2_key):
        return {"number": ep_idx, "videoUrl": f"{R2_PUBLIC}/{r2_key}", "status": "exists"}

    # Get video URL (prefer 720P)
    videos = ep.get("videos", [])
    video_url = None
    for q in ["720P", "540P", "480P", "360P"]:
        for v in videos:
            if v.get("quality") == q:
                video_url = v["url"]
                break
        if video_url:
            break
    if not video_url and videos:
        video_url = videos[0].get("url", "")
    if not video_url:
        tprint(f"    {tag} Ep {ep_idx:3}/{total_eps}: NO URL")
        return None

    work_dir = TEMP_DIR / f"{slug}_ep{ep_idx}_{threading.current_thread().ident}"
    work_dir.mkdir(exist_ok=True)
    raw_path = work_dir / "raw.mp4"
    fast_path = work_dir / "out.mp4"

    try:
        # Download
        r = requests.get(video_url, timeout=180, stream=True)
        r.raise_for_status()
        total = 0
        with open(raw_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
                total += len(chunk)
        if total < 1000:
            tprint(f"    {tag} Ep {ep_idx:3}/{total_eps}: TOO SMALL")
            return None

        raw_mb = total / 1024 / 1024

        # Faststart
        result = subprocess.run([
            "ffmpeg", "-y", "-i", str(raw_path),
            "-c", "copy", "-movflags", "+faststart",
            str(fast_path)
        ], capture_output=True, text=True, timeout=120)

        upload_file = fast_path if (result.returncode == 0 and fast_path.exists()) else raw_path

        # Upload
        s3.upload_file(str(upload_file), R2_BUCKET, r2_key,
            ExtraArgs={"ContentType": "video/mp4"})

        tprint(f"    {tag} Ep {ep_idx:3}/{total_eps}: OK {raw_mb:.1f}MB")
        return {"number": ep_idx, "videoUrl": f"{R2_PUBLIC}/{r2_key}", "status": "new"}

    except Exception as e:
        tprint(f"    {tag} Ep {ep_idx:3}/{total_eps}: FAIL {str(e)[:50]}")
        return None
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


def register_drama_db(title, desc, slug, total_eps, uploaded_eps):
    """Register drama and episodes to backend DB."""
    genres = infer_genres(title, desc)
    payload = {
        "title": title,
        "description": desc,
        "cover": f"{R2_PUBLIC}/microdrama/{slug}/cover.webp",
        "genres": genres,
        "status": "completed",
        "country": "China",
        "language": "Indonesia",
    }
    try:
        r = requests.post(f"{BACKEND_URL}/dramas", json=payload, timeout=15)
        if r.status_code not in [200, 201]:
            tprint(f"    DB drama FAIL: {r.status_code} {r.text[:60]}")
            return False
        drama_db_id = r.json().get("id")
        fail = 0
        for ep in sorted(uploaded_eps, key=lambda x: x["number"]):
            ep_payload = {
                "dramaId": drama_db_id,
                "episodeNumber": ep["number"],
                "title": f"Episode {ep['number']}",
                "videoUrl": ep["videoUrl"],
            }
            try:
                er = requests.post(f"{BACKEND_URL}/episodes", json=ep_payload, timeout=10)
                if er.status_code not in [200, 201]:
                    fail += 1
            except:
                fail += 1
        tprint(f"    DB: {len(uploaded_eps)} eps registered ({fail} fails)")
        return True
    except Exception as e:
        tprint(f"    DB error: {e}")
        return False


def process_drama(drama_data, detail, index, total, num_workers):
    """Process one drama: upload cover, download all episodes in parallel, register to DB."""
    title = drama_data["title"]
    desc = drama_data.get("description", "")
    slug = slugify(title)
    tag = f"[{index}/{total}]"

    episodes = detail.get("episodes", [])
    total_eps = len(episodes)

    tprint(f"\n{'=' * 60}")
    tprint(f"  {tag} {title}")
    tprint(f"  Slug: {slug} | Episodes: {total_eps}")

    if total_eps == 0:
        tprint(f"  {tag} No episodes!")
        with _stats_lock:
            stats["fail"] += 1
        return

    # Upload cover
    s3 = get_s3()
    cover_url = drama_data.get("cover", "")
    cover_key = f"microdrama/{slug}/cover.webp"
    if cover_url and not r2_key_exists(s3, cover_key):
        try:
            resp = requests.get(cover_url, timeout=15)
            if resp.status_code == 200 and len(resp.content) > 100:
                s3.put_object(Bucket=R2_BUCKET, Key=cover_key,
                    Body=resp.content,
                    ContentType=resp.headers.get("content-type", "image/jpeg"))
                tprint(f"  {tag} Cover: OK")
        except:
            tprint(f"  {tag} Cover: FAIL")
    else:
        tprint(f"  {tag} Cover: exists")

    # Save metadata
    metadata = {
        "title": title, "description": desc, "totalEpisodes": total_eps,
        "provider": "microdrama", "sourceId": drama_data["id"],
    }
    try:
        s3.put_object(Bucket=R2_BUCKET, Key=f"microdrama/{slug}/metadata.json",
            Body=json.dumps(metadata, ensure_ascii=False, indent=2).encode("utf-8"),
            ContentType="application/json")
    except:
        pass

    # Download episodes in parallel
    uploaded = []
    with ThreadPoolExecutor(max_workers=num_workers) as pool:
        futures = {pool.submit(download_ep, ep, slug, total_eps, tag): ep for ep in episodes}
        for f in as_completed(futures):
            result = f.result()
            if result:
                uploaded.append(result)
            else:
                with _stats_lock:
                    stats["ep_fail"] += 1

    # Register to DB if all episodes uploaded
    if len(uploaded) >= total_eps:
        if register_drama_db(title, desc, slug, total_eps, uploaded):
            with _stats_lock:
                stats["ok"] += 1
                stats["eps"] += len(uploaded)
        else:
            with _stats_lock:
                stats["fail"] += 1
        tprint(f"  {tag} DONE: {title} ({len(uploaded)}/{total_eps} eps)")
    elif uploaded:
        tprint(f"  {tag} PARTIAL: {len(uploaded)}/{total_eps} eps (skipping DB)")
        with _stats_lock:
            stats["eps"] += len(uploaded)
            stats["fail"] += 1
    else:
        tprint(f"  {tag} FAILED: no episodes")
        with _stats_lock:
            stats["fail"] += 1


def main():
    limit = 999  # Default: all
    num_workers = 8
    register_only = "--register-only" in sys.argv

    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        if idx + 1 < len(sys.argv):
            limit = int(sys.argv[idx + 1])
    if "--workers" in sys.argv:
        idx = sys.argv.index("--workers")
        if idx + 1 < len(sys.argv):
            num_workers = int(sys.argv[idx + 1])

    print("=" * 60, flush=True)
    print("  MICRODRAMA -> R2 SCRAPER (Indonesian)", flush=True)
    print(f"  Target: {'all' if limit >= 999 else limit} dramas | lang={LANG} | workers={num_workers}", flush=True)
    print(f"  Backend: {BACKEND_URL}", flush=True)
    print("=" * 60, flush=True)

    # Check ffmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=10)
    except:
        print("  ffmpeg not found!", flush=True)
        sys.exit(1)

    # Fetch drama list with lang=id
    print(f"\n  Fetching drama list (lang={LANG})...", flush=True)
    all_dramas = []
    offset = 0
    while len(all_dramas) < limit:
        batch = min(20, limit - len(all_dramas))
        try:
            r = requests.get(f"{API}?action=list&limit={batch}&offset={offset}&lang={LANG}", timeout=15)
            data = r.json()
            dramas = data.get("dramas", [])
            if not dramas:
                break
            all_dramas.extend(dramas)
            offset += len(dramas)
            print(f"    Fetched {len(all_dramas)} / {data.get('total', '?')}", flush=True)
        except Exception as e:
            print(f"    Fetch error: {e}", flush=True)
            break

    print(f"\n  Total available: {len(all_dramas)}", flush=True)

    # Check existing in R2
    s3 = get_s3()
    existing = set()
    try:
        paginator = s3.get_paginator('list_objects_v2')
        for page in paginator.paginate(Bucket=R2_BUCKET, Prefix="microdrama/", Delimiter="/"):
            for prefix in page.get("CommonPrefixes", []):
                slug = prefix["Prefix"].replace("microdrama/", "").rstrip("/")
                if slug:
                    existing.add(slug)
        print(f"  Already in R2: {len(existing)}", flush=True)
    except:
        pass

    # Process
    start = time.time()
    for i, drama in enumerate(all_dramas, 1):
        slug = slugify(drama["title"])
        if slug in existing and not register_only:
            tprint(f"\n  [{i}/{len(all_dramas)}] SKIP: {drama['title']} (exists)")
            stats["skipped"] += 1
            continue

        try:
            dr = requests.get(f"{API}?action=detail&id={drama['id']}&lang={LANG}", timeout=15)
            detail = dr.json()
        except:
            tprint(f"\n  [{i}/{len(all_dramas)}] Detail fetch failed: {drama['title']}")
            stats["fail"] += 1
            continue

        if register_only:
            # Just register existing R2 data to DB
            episodes = detail.get("episodes", [])
            total_eps = len(episodes)
            if slug in existing:
                uploaded = [{"number": ep.get("index", 0), "videoUrl": f"{R2_PUBLIC}/microdrama/{slug}/ep{ep.get('index',0):03d}.mp4"} for ep in episodes if ep.get("index", 0) > 0]
                if register_drama_db(drama["title"], drama.get("description", ""), slug, total_eps, uploaded):
                    stats["ok"] += 1
                    stats["eps"] += len(uploaded)
                    tprint(f"  [{i}/{len(all_dramas)}] Registered: {drama['title']} ({len(uploaded)} eps)")
                else:
                    stats["fail"] += 1
        else:
            process_drama(drama, detail, i, len(all_dramas), num_workers)

    elapsed = time.time() - start
    print(f"\n{'=' * 60}", flush=True)
    print(f"  DONE in {elapsed/60:.1f} minutes", flush=True)
    print(f"  Success: {stats['ok']} dramas, {stats['eps']} episodes", flush=True)
    print(f"  Failed:  {stats['fail']} dramas, {stats['ep_fail']} episodes", flush=True)
    print(f"  Skipped: {stats['skipped']}", flush=True)
    print(f"{'=' * 60}", flush=True)


if __name__ == "__main__":
    main()
