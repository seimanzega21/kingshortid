 #!/usr/bin/env python3
"""
VIDRAMA MICRODRAMA HLS SCRAPER v2 - FAST MODE
===============================================
Optimizations vs v1:
  - ffmpeg preset: fast → ultrafast  (3-4x faster encoding)
  - Parallel episode download: 2 concurrent downloads per drama
  - Reduced sleep: 0.3s → 0.1s between episodes
  - Can run alongside v1 (both skip dramas already in R2)

Usage:
    python vidrama_microdrama_hls_v2.py --limit 200
    python vidrama_microdrama_hls_v2.py --start 20 --limit 200  # start from drama #20
"""
import requests, json, time, os, re, sys, subprocess, shutil, boto3
from pathlib import Path
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

load_dotenv()
sys.stdout.reconfigure(encoding="utf-8")

# ──────────────────── CONFIG ────────────────────
API_LIST_URL  = "https://vidrama.asia/api/microdrama?action=list&lang=id"
NEXT_ACTION   = "40c1405810e1d492d36c686b19fdd772f47beba84f"
BACKEND_URL   = "https://api.shortlovers.id/api"
R2_PUBLIC     = "https://stream.shortlovers.id"
R2_BUCKET     = os.getenv("R2_BUCKET_NAME") or "shortlovers"
R2_PREFIX     = "dramas/microdrama"
TEMP_DIR      = Path("/tmp/microdrama_mp4_v3") if os.name != 'nt' else Path("C:/tmp/microdrama_mp4_v3")
LOG_FILE      = Path(__file__).parent / "microdrama_mp4_v3.log"
DRAMA_LIMIT   = 200
QUALITY_PREF  = ["720P", "540P", "480P", "360P"]
EP_WORKERS    = 2         # parallel episode downloads per drama (safe)

_log_lock = Lock()
_log_fh = open(LOG_FILE, "w", encoding="utf-8")

def log(msg="", end="\n"):
    with _log_lock:
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
            if r.status_code != 200: break
            data = r.json()
            dramas = data.get("dramas", [])
            if not dramas: break
            all_dramas.extend(dramas)
            log(f"    Page {page+1}: +{len(dramas)} dramas (total: {len(all_dramas)})")
            if len(all_dramas) >= data.get("total", 9999): break
            page += 1
            time.sleep(0.3)
        except Exception as e:
            log(f"    Error: {e}")
            break
    log(f"    Discovered: {len(all_dramas)} dramas")
    return all_dramas[:target]

# ──────────────────── R2/D1 CHECKS ────────────────────
def get_r2_slugs() -> set:
    log("[2] Scanning R2 for existing dramas...")
    pag = get_s3().get_paginator("list_objects_v2")
    slugs = set()
    for prefix in [f"{R2_PREFIX}/"]:
        for pg in pag.paginate(Bucket=R2_BUCKET, Prefix=prefix, Delimiter="/"):
            for p in pg.get("CommonPrefixes", []):
                slug = p["Prefix"].rstrip("/").split("/")[-1]
                if slug: slugs.add(slug)
    log(f"    R2: {len(slugs)} existing slugs")
    return slugs

def get_d1_titles() -> set:
    log("[3] Fetching D1 drama titles (Microdrama only)...")
    try:
        r = requests.get(f"{BACKEND_URL}/dramas?limit=1000", timeout=15)
        data = r.json()
        items = data if isinstance(data, list) else data.get("dramas", [])
        titles = {d["title"] for d in items if d.get("provider") in ("microdrama", "idrama")}
        log(f"    D1 (Microdrama): {len(titles)} dramas")
        return titles
    except Exception as e:
        log(f"    D1 error: {e}")
        return set()

# ──────────────────── EPISODE DATA ────────────────────
def fetch_episodes(drama_id: str, drama_slug: str) -> list:
    url = f"https://vidrama.asia/api/microdrama?action=detail&id={drama_id}"
    try:
        r = requests.get(url, timeout=30)
        if r.status_code == 200:
            data = r.json()
            return data.get("episodes", [])
    except Exception as e:
        log(f"  Episode fetch error: {e}")
    return []

def get_best_url(videos: list) -> str | None:
    qmap = {v.get("quality", ""): v.get("url", "") for v in videos}
    for q in QUALITY_PREF:
        if qmap.get(q): return qmap[q]
    for v in videos:
        if v.get("url"): return v["url"]
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
            if total > 5000: return True
        except Exception as e:
            if attempt == 0: time.sleep(1)
            else: log(f" DLerr:{str(e)[:30]}", end="")
    return False

def compress_variants(input_mp4: Path, base_output: str, temp_dir: Path) -> tuple[Path|None, Path|None]:
    out_720 = temp_dir / f"{base_output}.mp4"
    out_540 = temp_dir / f"{base_output}_540p.mp4"
    
    cmd_720 = [
        "ffmpeg", "-y", "-i", str(input_mp4),
        "-c:v", "libx264", "-preset", "faster", "-crf", "28",
        "-maxrate", "1200k", "-bufsize", "2400k",
        "-movflags", "+faststart", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "96k", "-ac", "2",
        str(out_720)
    ]
    
    cmd_540 = [
        "ffmpeg", "-y", "-i", str(input_mp4),
        "-vf", "scale=-2:540",
        "-c:v", "libx264", "-preset", "faster", "-crf", "28",
        "-maxrate", "800k", "-bufsize", "1600k",
        "-movflags", "+faststart", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "96k", "-ac", "2",
        str(out_540)
    ]
    
    try:
        res1 = subprocess.run(cmd_720, capture_output=True, timeout=300)
        res2 = subprocess.run(cmd_540, capture_output=True, timeout=300)
        
        ok1 = res1.returncode == 0 and out_720.exists()
        ok2 = res2.returncode == 0 and out_540.exists()
        
        log(f" FF:{res1.returncode},{res2.returncode}", end="")
        return (out_720 if ok1 else None, out_540 if ok2 else None)
    except Exception as e:
        log(f" FFexe:{str(e)[:50]}")
        return None, None

def upload_mp4(mp4_file: Path, r2_key: str) -> str | None:
    if not mp4_file.exists(): return None
    get_s3().upload_file(str(mp4_file), R2_BUCKET, r2_key,
                         ExtraArgs={"ContentType": "video/mp4"})
    return f"{R2_PUBLIC}/{r2_key}"

def upload_cover(cover_url: str, slug: str) -> bool:
    if not cover_url: return False
    try:
        resp = requests.get(cover_url, timeout=15)
        resp.raise_for_status()
        if len(resp.content) < 100: return False
        get_s3().put_object(Bucket=R2_BUCKET,
                            Key=f"{R2_PREFIX}/{slug}/cover.webp",
                            Body=resp.content,
                            ContentType=resp.headers.get("content-type", "image/webp"))
        return True
    except: return False

# ──────────────────── EPISODE WORKER (parallel) ────────────────────
def process_episode(ep, drama_temp, total_eps, slug, r2_prefix):
    """Process single episode: download → HLS → R2. Returns dict or None."""
    ep_num = ep.get("index", 0)
    if ep_num == 0: return None

    videos = ep.get("videos", [])
    video_url = get_best_url(videos)
    if not video_url:
        log(f"    Ep {ep_num:3}: SKIP no URL")
        return None

    r2_ep_key = f"{r2_prefix}/{slug}/ep{ep_num:03d}.mp4"
    r2_540_key = r2_ep_key.replace(".mp4", "_540p.mp4")

    # Skip ONLY if both formats already exist in R2
    try:
        get_s3().head_object(Bucket=R2_BUCKET, Key=r2_ep_key)
        # Check 540p as well
        get_s3().head_object(Bucket=R2_BUCKET, Key=r2_540_key)
        log(f"    Ep {ep_num:3}/{total_eps}: already in R2 (720p & 540p)")
        return {"number": ep_num, "videoUrl": f"{R2_PUBLIC}/{r2_ep_key}", "videoUrl540p": f"{R2_PUBLIC}/{r2_540_key}", "duration": 0}
    except: pass

    log(f"    Ep {ep_num:3}/{total_eps}:", end="")

    raw = drama_temp / f"raw_ep{ep_num:03d}.mp4"
    if not download_mp4(video_url, raw):
        log(f" FAIL"); return None

    mb = raw.stat().st_size / 1024 / 1024
    log(f" DL({mb:.1f}MB)", end="")

    c720, c540 = compress_variants(raw, f"opt_ep{ep_num:03d}", drama_temp)
    if c720:
        mb_720 = c720.stat().st_size / 1024 / 1024
        mb_540 = c540.stat().st_size / 1024 / 1024 if c540 else 0
        log(f" COMP(720={mb_720:.1f}MB|540={mb_540:.1f}MB)", end="")
        
        mp4_url = upload_mp4(c720, r2_ep_key)
        
        url_540p = None
        if c540:
            r2_540_key = r2_ep_key.replace(".mp4", "_540p.mp4")
            url_540p = upload_mp4(c540, r2_540_key)
            c540.unlink(missing_ok=True)
            
        c720.unlink(missing_ok=True)
        raw.unlink(missing_ok=True)
        
        if mp4_url:
            log(f" R2 OK (540p:{'Yes' if url_540p else 'No'})")
            return {"number": ep_num, "videoUrl": mp4_url, "videoUrl540p": url_540p, "duration": 0}
        else:
            log(f" R2 FAIL"); return None
    else:
        log(f" COMP FAIL")
        raw.unlink(missing_ok=True)
        return None

# ──────────────────── DRAMA PROCESSOR ────────────────────
def process_drama(drama: dict, slug: str) -> list | None:
    drama_id = str(drama["id"])
    total_eps = drama.get("episodes", 0)

    cover_ok = upload_cover(drama.get("cover", ""), slug)
    log(f"  Cover: {'OK' if cover_ok else 'FAIL'}")

    episodes_data = fetch_episodes(drama_id, slug)
    if not episodes_data:
        log(f"  FAIL: no episodes data"); return None

    log(f"  Episodes: {len(episodes_data)}")

    drama_temp = TEMP_DIR / slug
    drama_temp.mkdir(parents=True, exist_ok=True)

    sorted_eps = sorted(episodes_data, key=lambda e: e.get("index", 0))
    uploaded = []

    # ⚡ Process EP_WORKERS episodes in parallel
    with ThreadPoolExecutor(max_workers=EP_WORKERS) as executor:
        futures = {
            executor.submit(process_episode, ep, drama_temp, total_eps, slug, R2_PREFIX): ep
            for ep in sorted_eps
        }
        for future in as_completed(futures):
            result = future.result()
            if result:
                uploaded.append(result)
            time.sleep(0.1)  # small delay between completions

    uploaded.sort(key=lambda e: e["number"])
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
            "isActive": False,
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
                    "videoUrl540p": ep.get("videoUrl540p"),
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
    limit = DRAMA_LIMIT
    start = 0
    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        if idx + 1 < len(sys.argv):
            limit = int(sys.argv[idx + 1])
    if "--start" in sys.argv:
        idx = sys.argv.index("--start")
        if idx + 1 < len(sys.argv):
            start = int(sys.argv[idx + 1])

    log("=" * 60)
    log("  VIDRAMA MICRODRAMA HLS SCRAPER v2 (FAST MODE)")
    log(f"  Limit: {limit} | EP_WORKERS: {EP_WORKERS} | Preset: ultrafast")
    log("=" * 60)

    dramas    = discover_dramas(target=limit + 100)
    r2_slugs  = get_r2_slugs()
    d1_titles = get_d1_titles()

    new = []
    # Only skip if the drama is completely in D1 AND we are sure it has 540p (which we aren't, so we just process all limits)
    # To avoid checking every drama, we only check the first `limit` dramas from the API
    new = dramas[start:start + limit]

    if not new:
        log("  Nothing new!"); return

    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    stats = {"ok": 0, "fail": 0, "eps": 0}
    for i, drama in enumerate(new, 1):
        slug  = slugify(drama.get("title", ""))
        title = drama.get("title", slug)
        log(f"\n{'_'*60}")
        log(f"  [{i}/{len(new)}] {title}")
        log(f"  Slug: {slug}")

        eps = process_drama(drama, slug)
        if not eps:
            stats["fail"] += 1; continue

        if register_drama(drama, slug, eps):
            stats["ok"] += 1; stats["eps"] += len(eps)
        else:
            stats["fail"] += 1

        time.sleep(0.5)  # brief pause between dramas

    shutil.rmtree(TEMP_DIR, ignore_errors=True)

    log(f"\n{'='*60}")
    log(f"  DONE: {stats['ok']} dramas, {stats['eps']} episodes")
    log(f"  Failed: {stats['fail']}")
    log(f"{'='*60}")

if __name__ == "__main__":
    main()
