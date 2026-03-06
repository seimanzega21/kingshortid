#!/usr/bin/env python3
"""
VIDRAMA MICRODRAMA HLS SCRAPER (Indonesian)
============================================
- Discovers 190 Indonesian dramas via /api/microdrama?action=list&lang=id
- Gets episode video URLs via Next.js Server Action (POST)
- Downloads best quality MP4 (720P → 540P → 480P → 360P)  
- Converts to HLS (.m3u8 + .ts segments) using ffmpeg
- Uploads HLS to R2 under dramas/microdrama/{slug}/ep{NNN}/
- Registers drama + episodes in D1 via backend API
- Skips dramas already in R2

Usage:
    python vidrama_microdrama_hls.py              # Full run, 200 drama limit
    python vidrama_microdrama_hls.py --limit 5   # Test with 5
    python vidrama_microdrama_hls.py --dry-run   # Discover only, no download
"""
import requests, json, time, os, re, sys, subprocess, shutil, boto3
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.stdout.reconfigure(encoding="utf-8")

# ──────────────────── CONFIG ────────────────────
API_LIST_URL  = "https://vidrama.asia/api/microdrama?action=list&lang=id"
NEXT_ACTION   = "40c1405810e1d492d36c686b19fdd772f47beba84f"
BACKEND_URL   = "https://api.shortlovers.id/api"
R2_PUBLIC     = "https://stream.shortlovers.id"
R2_BUCKET     = os.getenv("R2_BUCKET_NAME") or "shortlovers"
R2_PREFIX     = "dramas/microdrama"
TEMP_DIR      = Path("C:/tmp/microdrama_hls")
LOG_FILE      = Path(__file__).parent / "microdrama_hls.log"
DRAMA_LIMIT   = 200
HLS_SEG_DUR   = 4    # seconds per HLS segment
QUALITY_PREF  = ["720P", "540P", "480P", "360P"]

_log_fh = open(LOG_FILE, "w", encoding="utf-8")
def log(msg="", end="\n"):
    try: print(msg, end=end, flush=True)
    except: pass
    _log_fh.write(msg + end)
    _log_fh.flush()

# ──────────────────── HELPERS ────────────────────
def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")

_s3 = None
def get_s3():
    global _s3
    if _s3 is None:
        _s3 = boto3.client("s3",
            endpoint_url=os.getenv("R2_ENDPOINT"),
            aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
            region_name="auto",
        )
    return _s3

# ──────────────────── DISCOVERY ────────────────────
def discover_dramas(target=200) -> list:
    log("[1] Discovering Indonesian MicroDrama dramas...")
    all_dramas = []
    page = 0
    while len(all_dramas) < target:
        try:
            r = requests.get(f"{API_LIST_URL}&limit=50&offset={page * 50}", timeout=30)
            if r.status_code != 200:
                break
            data = r.json()
            dramas = data.get("dramas", [])
            if not dramas:
                break
            all_dramas.extend(dramas)
            log(f"    Page {page+1}: +{len(dramas)} dramas (total: {len(all_dramas)})")
            if len(all_dramas) >= data.get("total", 9999):
                break
            page += 1
            time.sleep(0.3)
        except Exception as e:
            log(f"    Error: {e}")
            break

    log(f"    Discovered: {len(all_dramas)} dramas")
    with open("microdrama_id_dramas.json", "w", encoding="utf-8") as f:
        json.dump(all_dramas, f, indent=2, ensure_ascii=False)
    return all_dramas[:target]

# ──────────────────── R2/D1 CHECKS ────────────────────
def get_r2_slugs() -> set:
    log("[2] Scanning R2 for existing dramas...")
    pag = get_s3().get_paginator("list_objects_v2")
    slugs = set()
    for prefix in ["melolo/", "dramas/melolo/", f"{R2_PREFIX}/"]:
        for pg in pag.paginate(Bucket=R2_BUCKET, Prefix=prefix, Delimiter="/"):
            for p in pg.get("CommonPrefixes", []):
                slug = p["Prefix"].rstrip("/").split("/")[-1]
                if slug: slugs.add(slug)
    log(f"    R2: {len(slugs)} existing slugs")
    return slugs

def get_d1_titles() -> set:
    log("[3] Fetching D1 drama titles...")
    try:
        r = requests.get(f"{BACKEND_URL}/dramas?limit=1000", timeout=15)
        data = r.json()
        items = data if isinstance(data, list) else data.get("dramas", [])
        titles = {d["title"] for d in items}
        log(f"    D1: {len(titles)} dramas")
        return titles
    except Exception as e:
        log(f"    D1 error: {e}")
        return set()

# ──────────────────── EPISODE DATA ────────────────────
def fetch_episodes(drama_id: str, drama_slug: str) -> list:
    """Use Next.js Server Action to get episode list with video URLs."""
    watch_url = f"https://vidrama.asia/watch/{drama_slug}--{drama_id}/1?provider=microdrama"
    headers = {
        "next-action": NEXT_ACTION,
        "accept": "text/x-component",
        "content-type": "text/plain;charset=UTF-8",
        "origin": "https://vidrama.asia",
        "referer": watch_url,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }
    try:
        r = requests.post(watch_url, headers=headers,
                          data=json.dumps([drama_id]).encode("utf-8"), timeout=30)
        if r.status_code != 200:
            return []
        # Parse RSC: "0:{...}\n1:[...]\n"
        for line in r.text.split("\n"):
            if ":" not in line: continue
            idx, _, rest = line.partition(":")
            if idx.strip().isdigit() and rest:
                try:
                    chunk = json.loads(rest)
                    if isinstance(chunk, dict) and "episodes" in chunk:
                        return chunk["episodes"]
                    if isinstance(chunk, list) and chunk and isinstance(chunk[0], dict) and "videos" in chunk[0]:
                        return chunk
                except:
                    pass
    except Exception as e:
        log(f"  Episode fetch error: {e}")
    return []

def get_best_url(videos: list) -> str | None:
    qmap = {v.get("quality", ""): v.get("url", "") for v in videos}
    for q in QUALITY_PREF:
        if qmap.get(q):
            return qmap[q]
    for v in videos:
        if v.get("url"):
            return v["url"]
    return None

# ──────────────────── VIDEO PROCESSING ────────────────────
def download_mp4(url: str, dest: Path) -> bool:
    for attempt in range(2):
        try:
            resp = requests.get(url, timeout=120, stream=True)
            resp.raise_for_status()
            total = 0
            with open(dest, "wb") as f:
                for chunk in resp.iter_content(chunk_size=2 * 1024 * 1024):
                    f.write(chunk); total += len(chunk)
            if total > 5000:
                return True
        except Exception as e:
            if attempt == 0: time.sleep(2)
            else: log(f" DLerr:{str(e)[:30]}", end="")
    return False

def convert_to_hls(input_mp4: Path, hls_dir: Path) -> bool:
    hls_dir.mkdir(parents=True, exist_ok=True)
    m3u8 = hls_dir / "index.m3u8"
    cmd = [
        "ffmpeg", "-y", "-i", str(input_mp4),
        "-c:v", "libx264", "-preset", "fast", "-crf", "28",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-ac", "2",
        "-hls_time", str(HLS_SEG_DUR),
        "-hls_playlist_type", "vod",
        "-hls_segment_filename", str(hls_dir / "seg%04d.ts"),
        "-hls_flags", "independent_segments",
        str(m3u8)
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, timeout=600)
        return res.returncode == 0 and m3u8.exists()
    except:
        return False

def upload_hls(hls_dir: Path, r2_ep_prefix: str) -> str | None:
    m3u8_file = hls_dir / "index.m3u8"
    if not m3u8_file.exists():
        return None
    ts_files = sorted(hls_dir.glob("*.ts"))
    for ts in ts_files:
        get_s3().upload_file(str(ts), R2_BUCKET, f"{r2_ep_prefix}/{ts.name}",
                             ExtraArgs={
                                 "ContentType": "video/MP2T",
                                 "CacheControl": "public, max-age=31536000, immutable",
                             })
    # Rewrite m3u8 with public R2 URLs
    content = m3u8_file.read_text()
    for ts in ts_files:
        content = content.replace(ts.name, f"{R2_PUBLIC}/{r2_ep_prefix}/{ts.name}")
    m3u8_key = f"{r2_ep_prefix}/index.m3u8"
    get_s3().put_object(Bucket=R2_BUCKET, Key=m3u8_key,
                        Body=content.encode("utf-8"),
                        ContentType="application/vnd.apple.mpegurl",
                        CacheControl="public, max-age=31536000, immutable")
    return f"{R2_PUBLIC}/{m3u8_key}"

def upload_cover(cover_url: str, slug: str) -> bool:
    if not cover_url: return False
    try:
        resp = requests.get(cover_url, timeout=15)
        resp.raise_for_status()
        if len(resp.content) < 100: return False
        get_s3().put_object(Bucket=R2_BUCKET,
                            Key=f"{R2_PREFIX}/{slug}/cover.webp",
                            Body=resp.content,
                            ContentType=resp.headers.get("content-type", "image/webp"),
                            CacheControl="public, max-age=86400")
        return True
    except:
        return False

# ──────────────────── DRAMA PROCESSOR ────────────────────
def process_drama(drama: dict, slug: str, dry_run: bool) -> list | None:
    drama_id = str(drama["id"])
    total_eps = drama.get("episodes", 0)

    cover_ok = False if dry_run else upload_cover(drama.get("cover", ""), slug)
    if not dry_run:
        log(f"  Cover: {'OK' if cover_ok else 'FAIL'}")

    # Fetch episode data
    episodes_data = fetch_episodes(drama_id, slug)
    if not episodes_data:
        log(f"  FAIL: no episodes data from Server Action")
        return None

    log(f"  Episodes: {len(episodes_data)}")
    if dry_run:
        return [{"number": ep.get("index", i+1), "videoUrl": "dry-run", "duration": 0}
                for i, ep in enumerate(episodes_data)]

    drama_temp = TEMP_DIR / slug
    drama_temp.mkdir(parents=True, exist_ok=True)
    uploaded = []

    for ep in sorted(episodes_data, key=lambda e: e.get("index", 0)):
        ep_num = ep.get("index", 0)
        if ep_num == 0: continue
        videos = ep.get("videos", [])
        video_url = get_best_url(videos)
        if not video_url:
            log(f"    Ep {ep_num:3}: SKIP no URL")
            continue

        r2_ep_prefix = f"{R2_PREFIX}/{slug}/ep{ep_num:03d}"
        m3u8_r2_key  = f"{r2_ep_prefix}/index.m3u8"

        # Skip if already in R2
        try:
            get_s3().head_object(Bucket=R2_BUCKET, Key=m3u8_r2_key)
            log(f"    Ep {ep_num:3}/{total_eps}: already in R2")
            uploaded.append({"number": ep_num,
                             "videoUrl": f"{R2_PUBLIC}/{m3u8_r2_key}", "duration": 0})
            continue
        except: pass

        log(f"    Ep {ep_num:3}/{total_eps}:", end="")

        # Download
        raw = drama_temp / f"raw_ep{ep_num:03d}.mp4"
        if not download_mp4(video_url, raw):
            log(f" FAIL"); time.sleep(0.5); continue

        mb = raw.stat().st_size / 1024 / 1024
        log(f" DL({mb:.1f}MB)", end="")

        # HLS
        hls_dir = drama_temp / f"hls_ep{ep_num:03d}"
        if convert_to_hls(raw, hls_dir):
            segs = len(list(hls_dir.glob("*.ts")))
            log(f" HLS({segs}seg)", end="")
            m3u8_url = upload_hls(hls_dir, r2_ep_prefix)
            shutil.rmtree(hls_dir, ignore_errors=True)
            if m3u8_url:
                log(f" R2 OK")
                uploaded.append({"number": ep_num, "videoUrl": m3u8_url, "duration": 0})
            else:
                log(f" R2 FAIL")
        else:
            log(f" HLS FAIL")

        raw.unlink(missing_ok=True)
        time.sleep(0.3)

    shutil.rmtree(drama_temp, ignore_errors=True)
    return uploaded if uploaded else None

# ──────────────────── D1 REGISTRATION ────────────────────
def register_drama(drama: dict, slug: str, episodes: list) -> bool:
    title = drama.get("title", slug)
    cover = f"{R2_PUBLIC}/{R2_PREFIX}/{slug}/cover.webp"
    try:
        resp = requests.post(f"{BACKEND_URL}/dramas", json={
            "title": title,
            "description": drama.get("description", ""),
            "cover": cover,
            "provider": "microdrama",
            "totalEpisodes": len(episodes),
            "isActive": True,
        }, timeout=15)
        if resp.status_code not in [200, 201]:
            log(f"  Drama register FAIL: {resp.status_code} {resp.text[:60]}")
            return False
        did = resp.json().get("id")
        ep_ok = 0
        for ep in episodes:
            try:
                er = requests.post(f"{BACKEND_URL}/episodes", json={
                    "dramaId": did,
                    "episodeNumber": ep["number"],
                    "videoUrl": ep["videoUrl"],
                    "duration": 0,
                }, timeout=10)
                if er.status_code in [200, 201]: ep_ok += 1
            except: pass
        log(f"  REGISTERED: {title} (id={did}, {ep_ok}/{len(episodes)} eps)")
        return True
    except Exception as e:
        log(f"  Register error: {e}")
        return False

# ──────────────────── MAIN ────────────────────
def main():
    dry_run = "--dry-run" in sys.argv
    limit = DRAMA_LIMIT
    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        if idx + 1 < len(sys.argv):
            limit = int(sys.argv[idx + 1])

    log("=" * 60)
    log("  VIDRAMA MICRODRAMA HLS SCRAPER (Indonesian)")
    log(f"  Limit: {limit} | Dry-run: {dry_run}")
    log("=" * 60)

    dramas   = discover_dramas(target=limit + 100)  # buffer for skips
    r2_slugs = get_r2_slugs()
    d1_titles = get_d1_titles()

    new = []
    for d in dramas:
        slug  = slugify(d.get("title", ""))
        title = d.get("title", "")
        if slug in r2_slugs or title in d1_titles:
            continue
        new.append(d)

    log(f"    New to scrape: {len(new)} -> capped at {limit}")
    new = new[:limit]

    if not new:
        log("  Nothing new!")
        return

    if not dry_run:
        TEMP_DIR.mkdir(parents=True, exist_ok=True)

    stats = {"ok": 0, "fail": 0, "eps": 0}
    for i, drama in enumerate(new, 1):
        slug  = slugify(drama.get("title", ""))
        title = drama.get("title", slug)
        log(f"\n{'_'*60}")
        log(f"  [{i}/{len(new)}] {title}")
        log(f"  Slug: {slug}")

        eps = process_drama(drama, slug, dry_run)
        if not eps:
            stats["fail"] += 1; continue

        if not dry_run:
            if register_drama(drama, slug, eps):
                stats["ok"] += 1; stats["eps"] += len(eps)
            else:
                stats["fail"] += 1
        else:
            log(f"  DRY-RUN: {len(eps)} episodes found")
            stats["ok"] += 1; stats["eps"] += len(eps)

        time.sleep(0.5)

    if not dry_run:
        shutil.rmtree(TEMP_DIR, ignore_errors=True)

    log(f"\n{'='*60}")
    log(f"  DONE: {stats['ok']} dramas, {stats['eps']} episodes")
    log(f"  Failed: {stats['fail']}")
    log(f"{'='*60}")

if __name__ == "__main__":
    main()
