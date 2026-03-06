#!/usr/bin/env python3
"""
RESCRAPE EPISODE 16 & 17 - LEGENDA NAGA KEMBALI
================================================
Drama ID  : 2010948201357684738
URL       : https://vidrama.asia/movie/legenda-naga-kembali--2010948201357684738?provider=microdrama
Slug      : legenda-naga-kembali
Provider  : microdrama

Script ini:
1. Ambil data episode 16 & 17 dari API microdrama
2. Download MP4 + faststart
3. Upload ke R2
4. Update/tambah record di D1 via backend API

Usage:
    python rescrape_legenda_naga.py           # scrape ep 16 & 17
    python rescrape_legenda_naga.py --dry-run # cek URL saja, tidak download
"""
import requests, json, time, os, re, sys, shutil, subprocess
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.stdout.reconfigure(encoding="utf-8")

# ─── CONFIG ────────────────────────────────────────────
DRAMA_ID    = "2010948201357684738"
DRAMA_SLUG  = "legenda-naga-kembali"
DRAMA_TITLE = "Legenda Naga Kembali"
TARGET_EPS  = [16, 17]           # episode yang mau di-rescrape

NEXT_ACTION  = "40c1405810e1d492d36c686b19fdd772f47beba84f"
BACKEND_URL  = "https://api.shortlovers.id/api"
R2_PUBLIC    = "https://stream.shortlovers.id"
R2_BUCKET    = os.getenv("R2_BUCKET_NAME", "shortlovers")
R2_PREFIX    = "dramas/microdrama"   # path di vidrama_mp4.py
R2_PREFIX_OLD = "microdrama"         # path di microdrama_scraper.py (lama)
TEMP_DIR     = Path("C:/tmp/legenda_naga_rescrape")
QUALITY_PREF = ["720P", "540P", "480P", "360P"]

DRY_RUN = "--dry-run" in sys.argv

# ─── S3 CLIENT ─────────────────────────────────────────
def get_s3():
    import boto3
    return boto3.client("s3",
        endpoint_url=os.getenv("R2_ENDPOINT"),
        aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
        region_name="auto",
    )

def r2_exists(s3, key):
    try:
        s3.head_object(Bucket=R2_BUCKET, Key=key)
        return True
    except:
        return False

# ─── CHECK FFMPEG ──────────────────────────────────────
def has_ffmpeg():
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
        return True
    except:
        return False

# ─── FETCH EPISODE LIST ────────────────────────────────
def fetch_episodes():
    """Ambil daftar episode dari API microdrama vidrama.asia"""
    print(f"[1] Fetching episode list for drama ID: {DRAMA_ID}")

    watch_url = f"https://vidrama.asia/watch/{DRAMA_SLUG}--{DRAMA_ID}/1?provider=microdrama"
    headers = {
        "next-action": NEXT_ACTION,
        "accept": "text/x-component",
        "content-type": "text/plain;charset=UTF-8",
        "origin": "https://vidrama.asia",
        "referer": watch_url,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    try:
        resp = requests.post(
            watch_url,
            headers=headers,
            data=json.dumps([DRAMA_ID]).encode("utf-8"),
            timeout=30
        )
        print(f"    Status: {resp.status_code}")
        if resp.status_code != 200:
            print(f"    ERROR: {resp.text[:200]}")
            return []

        # Parse RSC response (Next.js format)
        for line in resp.text.split("\n"):
            if ":" not in line:
                continue
            idx, _, rest = line.partition(":")
            if idx.strip().isdigit() and rest:
                try:
                    chunk = json.loads(rest)
                    if isinstance(chunk, dict) and "episodes" in chunk:
                        eps = chunk["episodes"]
                        print(f"    Found {len(eps)} episodes (from dict)")
                        return eps
                    if isinstance(chunk, list) and chunk and isinstance(chunk[0], dict) and "videos" in chunk[0]:
                        print(f"    Found {len(chunk)} episodes (from list)")
                        return chunk
                except:
                    pass

        print("    WARNING: No episodes found in response")
        print(f"    Response preview: {resp.text[:500]}")
        return []

    except Exception as e:
        print(f"    Error: {e}")
        return []

# ─── ALSO TRY DIRECT API ───────────────────────────────
def fetch_episodes_api():
    """Fallback: ambil dari API detail langsung"""
    print(f"[1b] Trying direct API for drama ID: {DRAMA_ID}")
    try:
        url = f"https://vidrama.asia/api/microdrama?action=detail&id={DRAMA_ID}&lang=id"
        resp = requests.get(url, timeout=20)
        print(f"    Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            eps = data.get("episodes", [])
            if eps:
                print(f"    Found {len(eps)} episodes via API")
                return eps
    except Exception as e:
        print(f"    API Error: {e}")
    return []

# ─── GET BEST URL ──────────────────────────────────────
def get_best_url(videos):
    qmap = {v.get("quality", ""): v.get("url", "") for v in videos}
    for q in QUALITY_PREF:
        if qmap.get(q):
            return qmap[q], q
    for v in videos:
        if v.get("url"):
            return v["url"], "unknown"
    return None, None

# ─── DOWNLOAD MP4 ──────────────────────────────────────
def download_mp4(url, dest):
    """Download dan apply ffmpeg faststart"""
    for attempt in range(3):
        try:
            print(f"    Downloading: {url[:80]}...")
            resp = requests.get(url, timeout=180, stream=True)
            resp.raise_for_status()

            total = 0
            raw = dest.with_suffix('.raw.mp4')
            with open(raw, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=4 * 1024 * 1024):
                    f.write(chunk)
                    total += len(chunk)

            if total < 5000:
                raw.unlink(missing_ok=True)
                print(f"    TOO SMALL: {total} bytes, retry...")
                continue

            print(f"    Downloaded: {total / 1024 / 1024:.1f} MB")

            # Apply faststart
            if has_ffmpeg():
                print(f"    Applying faststart...")
                result = subprocess.run(
                    ["ffmpeg", "-y", "-i", str(raw),
                     "-c", "copy", "-movflags", "+faststart", str(dest)],
                    capture_output=True, timeout=120
                )
                raw.unlink(missing_ok=True)
                if result.returncode == 0 and dest.exists():
                    print(f"    Faststart: OK")
                else:
                    print(f"    Faststart failed, using raw file")
                    if raw.exists():
                        raw.rename(dest)
            else:
                print(f"    ffmpeg not found, using raw file")
                raw.rename(dest)

            return dest.stat().st_size

        except Exception as e:
            print(f"    Attempt {attempt+1} failed: {e}")
            if attempt < 2:
                time.sleep(3)

    return 0

# ─── UPLOAD R2 ─────────────────────────────────────────
def upload_r2(s3, src, r2_key):
    print(f"    Uploading to R2: {r2_key}")
    try:
        s3.upload_file(
            str(src), R2_BUCKET, r2_key,
            ExtraArgs={
                "ContentType": "video/mp4",
                "CacheControl": "public, max-age=31536000, immutable",
                "ContentDisposition": "inline",
            }
        )
        return f"{R2_PUBLIC}/{r2_key}"
    except Exception as e:
        print(f"    R2 upload error: {e}")
        return None

# ─── GET DRAMA ID FROM DB ──────────────────────────────
def get_drama_db_id():
    """Cari drama ID di D1 database"""
    print(f"[3] Looking up drama in D1 database...")
    try:
        # Try by title
        resp = requests.get(f"{BACKEND_URL}/dramas?limit=500", timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            items = data if isinstance(data, list) else data.get("dramas", [])
            for d in items:
                if d.get("title", "").lower() == DRAMA_TITLE.lower():
                    print(f"    Found drama ID: {d['id']} (title match)")
                    return d["id"]
            # Fuzzy match - legenda
            for d in items:
                if "legenda" in d.get("title", "").lower() and "naga" in d.get("title", "").lower():
                    print(f"    Found drama ID: {d['id']} (fuzzy: {d['title']})")
                    return d["id"]
        print(f"    Drama NOT found in D1! Need to register first.")
        return None
    except Exception as e:
        print(f"    D1 lookup error: {e}")
        return None

# ─── UPDATE EPISODE IN DB ──────────────────────────────
def update_episode_db(drama_db_id, ep_num, video_url):
    """Update atau insert episode di D1"""
    payload = {
        "dramaId": drama_db_id,
        "episodeNumber": ep_num,
        "title": f"Episode {ep_num}",
        "videoUrl": video_url,
        "duration": 0,
    }

    # Try PATCH first (update existing)
    try:
        resp = requests.patch(
            f"{BACKEND_URL}/episodes/{drama_db_id}/{ep_num}",
            json=payload, timeout=10
        )
        if resp.status_code in [200, 201]:
            print(f"    DB PATCH OK (ep {ep_num})")
            return True
    except:
        pass

    # Try POST (create new)
    try:
        resp = requests.post(f"{BACKEND_URL}/episodes", json=payload, timeout=10)
        if resp.status_code in [200, 201]:
            print(f"    DB POST OK (ep {ep_num})")
            return True
        else:
            print(f"    DB POST failed: {resp.status_code} {resp.text[:100]}")
    except Exception as e:
        print(f"    DB error: {e}")

    return False

# ─── FIND DRAMA IN R2 ──────────────────────────────────
def check_r2_status(s3):
    """Cek status episode 16 & 17 di R2"""
    print(f"[2] Checking R2 status...")
    results = {}
    for ep_num in TARGET_EPS:
        # Check both possible R2 paths
        key_new = f"{R2_PREFIX}/{DRAMA_SLUG}/ep{ep_num:03d}/video.mp4"
        key_old = f"{R2_PREFIX_OLD}/{DRAMA_SLUG}/ep{ep_num:03d}.mp4"
        
        if r2_exists(s3, key_new):
            results[ep_num] = {"exists": True, "key": key_new, "url": f"{R2_PUBLIC}/{key_new}"}
            print(f"    Ep {ep_num:3}: EXISTS (new path) → {key_new}")
        elif r2_exists(s3, key_old):
            results[ep_num] = {"exists": True, "key": key_old, "url": f"{R2_PUBLIC}/{key_old}"}
            print(f"    Ep {ep_num:3}: EXISTS (old path) → {key_old}")
        else:
            results[ep_num] = {"exists": False}
            print(f"    Ep {ep_num:3}: MISSING from R2")
    return results

# ─── MAIN ──────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  RESCRAPE: Legenda Naga Kembali - Ep 16 & 17")
    print(f"  Drama ID : {DRAMA_ID}")
    print(f"  Slug     : {DRAMA_SLUG}")
    print(f"  Dry-run  : {DRY_RUN}")
    print("=" * 60)

    s3 = get_s3()

    # Step 1: Check R2 status
    r2_status = check_r2_status(s3)

    # Step 2: Fetch episodes dari API
    episodes = fetch_episodes()
    if not episodes:
        print("\n  Trying fallback API...")
        episodes = fetch_episodes_api()

    if not episodes:
        print("\n  ERROR: Could not fetch episodes! Check network/API.")
        sys.exit(1)

    print(f"\n  Total episodes found: {len(episodes)}")

    # Step 3: Filter hanya ep 16 & 17
    target_eps_data = []
    for ep in episodes:
        idx = ep.get("index", 0)
        if idx in TARGET_EPS:
            videos = ep.get("videos", [])
            url, quality = get_best_url(videos)
            print(f"  Ep {idx:3}: {'has URL' if url else 'NO URL'} | quality={quality} | videos={len(videos)}")
            if url:
                target_eps_data.append({"index": idx, "url": url, "quality": quality})

    if not target_eps_data:
        print(f"\n  ERROR: Episode 16 dan 17 tidak ada URL video di API!")
        print(f"  Raw episode data untuk TARGET_EPS:")
        for ep in episodes:
            if ep.get("index") in TARGET_EPS:
                print(f"    {json.dumps(ep, indent=2)[:300]}")
        sys.exit(1)

    if DRY_RUN:
        print("\n  === DRY RUN MODE ===")
        for ep in target_eps_data:
            print(f"  Ep {ep['index']:3}: {ep['url'][:80]} ({ep['quality']})")
        print("  DRY RUN selesai. Tambahkan tanpa --dry-run untuk eksekusi.")
        return

    # Step 4: Download & Upload
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    uploaded = {}

    for ep in target_eps_data:
        ep_num = ep["index"]
        r2_key = f"{R2_PREFIX}/{DRAMA_SLUG}/ep{ep_num:03d}/video.mp4"

        print(f"\n{'─'*50}")
        print(f"  Processing Episode {ep_num}...")

        # Cek kalau sudah ada di R2
        if r2_status.get(ep_num, {}).get("exists"):
            existing_url = r2_status[ep_num]["url"]
            print(f"  Ep {ep_num} sudah ada di R2, force overwrite...")

        # Download
        dest = TEMP_DIR / f"ep{ep_num:03d}.mp4"
        size = download_mp4(ep["url"], dest)
        if not size:
            print(f"  FAIL: Download episode {ep_num} gagal!")
            continue

        # Upload to R2
        video_url = upload_r2(s3, dest, r2_key)
        dest.unlink(missing_ok=True)

        if video_url:
            uploaded[ep_num] = video_url
            print(f"  Ep {ep_num}: UPLOADED → {video_url}")
        else:
            print(f"  Ep {ep_num}: R2 UPLOAD FAILED!")

    # Step 5: Update DB
    if uploaded:
        print(f"\n{'─'*50}")
        drama_db_id = get_drama_db_id()

        if drama_db_id:
            for ep_num, video_url in uploaded.items():
                update_episode_db(drama_db_id, ep_num, video_url)
        else:
            print("  WARNING: Drama tidak ditemukan di DB!")
            print("  Perlu daftar drama dulu atau cek API backend.")
            print("  Video sudah di R2, URL-nya:")
            for ep_num, url in uploaded.items():
                print(f"    Ep {ep_num}: {url}")

    # Cleanup
    shutil.rmtree(TEMP_DIR, ignore_errors=True)

    print(f"\n{'='*60}")
    print(f"  SELESAI!")
    print(f"  Berhasil upload: {list(uploaded.keys())}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
