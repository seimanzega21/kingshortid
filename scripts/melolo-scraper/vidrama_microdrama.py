#!/usr/bin/env python3
"""
VIDRAMA MICRODRAMA SCRAPER
==========================
Scrapes NEW dramas from vidrama.asia/provider/microdrama API,
downloads MP4 via proxy, transcodes via ffmpeg, uploads to R2,
and registers in D1.

Checks R2 first to skip existing dramas.
"""
import requests, json, time, os, re, sys, subprocess, tempfile, shutil, boto3
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.stdout.reconfigure(encoding="utf-8")

# Config
API_URL = "https://vidrama.asia/api/microdrama"
BACKEND_URL = "https://api.shortlovers.id/api"
R2_PUBLIC = "https://stream.shortlovers.id"
R2_BUCKET = os.getenv("R2_BUCKET_NAME") or "shortlovers"
R2_PREFIX = "dramas/microdrama"  # New prefix for microdrama provider

LOG_FILE = Path(__file__).parent / "microdrama_scrape.log"
_log_fh = open(LOG_FILE, "w", encoding="utf-8")

def log(msg="", end="\n", flush=True):
    try:
        print(msg, end=end, flush=flush)
    except:
        pass
    _log_fh.write(msg + end)
    if flush:
        _log_fh.flush()

# S3/R2 client
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

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")

# ---- DISCOVERY ----
def discover_dramas():
    """Get all dramas from microdrama list API."""
    log("[1] Discovering microdrama dramas...")
    all_dramas = []
    page_num = 0
    while True:
        try:
            r = requests.get(f"{API_URL}?action=list&limit=50&offset={page_num * 50}", timeout=30)
            if r.status_code != 200:
                log(f"    List API returned {r.status_code}, stopping")
                break
            data = r.json()
            dramas = data.get("dramas", [])
            if not dramas:
                break
            all_dramas.extend(dramas)
            log(f"    Page {page_num+1}: +{len(dramas)} dramas (total: {len(all_dramas)})")
            if len(dramas) < 50:
                break
            page_num += 1
            time.sleep(0.3)
        except Exception as e:
            log(f"    Error: {e}")
            break
    log(f"    Total discovered: {len(all_dramas)}")
    return all_dramas

# ---- R2 CHECK ----
def get_r2_slugs():
    """Get existing drama slugs from R2."""
    log("[2] Checking existing R2 dramas...")
    s3 = get_s3()
    paginator = s3.get_paginator("list_objects_v2")
    slugs = set()
    # Check both old and new prefixes
    for prefix in ["melolo/", "dramas/melolo/", f"{R2_PREFIX}/"]:
        for page in paginator.paginate(Bucket=R2_BUCKET, Prefix=prefix, Delimiter="/"):
            for p in page.get("CommonPrefixes", []):
                parts = p["Prefix"].rstrip("/").split("/")
                slug = parts[-1]
                if slug:
                    slugs.add(slug)
    log(f"    R2 has {len(slugs)} existing drama slugs")
    return slugs

# ---- D1 CHECK ----
def get_d1_titles():
    """Get existing drama titles from D1."""
    log("[3] Checking existing D1 dramas...")
    try:
        r = requests.get(f"{BACKEND_URL}/dramas?limit=1000", timeout=15)
        data = r.json()
        items = data if isinstance(data, list) else data.get("dramas", [])
        titles = {d["title"] for d in items}
        log(f"    D1 has {len(titles)} dramas")
        return titles
    except Exception as e:
        log(f"    D1 error: {e}")
        return set()

# ---- SCRAPING ----
TEMP_DIR = Path(tempfile.gettempdir()) / "microdrama_scrape"

def transcode_video(input_path, output_path):
    cmd = [
        "ffmpeg", "-y", "-i", str(input_path),
        "-c:v", "libx264", "-preset", "fast", "-crf", "28",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-ac", "2",
        "-movflags", "+faststart",
        str(output_path)
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 1000
    except:
        return False

def process_drama(drama, slug):
    """Download, transcode, upload a single drama."""
    drama_id = drama["id"]
    title = drama.get("title", slug)

    # Get detail + episodes
    try:
        r = requests.get(f"{API_URL}?action=detail&id={drama_id}", timeout=30)
        if r.status_code != 200:
            log(f"  Detail API failed: {r.status_code}")
            return None
        detail = r.json().get("data", {})
    except Exception as e:
        log(f"  Detail error: {e}")
        return None

    episodes = detail.get("episodes", [])
    if not episodes:
        log(f"  No episodes")
        return None

    total_eps = len(episodes)
    desc = drama.get("description", "") or detail.get("description", "")
    log(f"  Desc: {desc[:70]}...")
    log(f"  Episodes: {total_eps}")

    # Upload cover
    cover_url = drama.get("image") or drama.get("poster", "")
    cover_ok = False
    if cover_url:
        try:
            resp = requests.get(cover_url, timeout=15)
            resp.raise_for_status()
            if len(resp.content) > 100:
                get_s3().put_object(
                    Bucket=R2_BUCKET, Key=f"{R2_PREFIX}/{slug}/cover.webp",
                    Body=resp.content,
                    ContentType=resp.headers.get("content-type", "image/webp")
                )
                cover_ok = True
        except:
            pass
    log(f"  Cover: {'OK' if cover_ok else 'FAIL'}")

    # Process episodes
    uploaded = []
    drama_temp = TEMP_DIR / slug
    drama_temp.mkdir(exist_ok=True, parents=True)

    for ep in episodes:
        ep_num = ep.get("episodeNumber", 0)
        if ep_num == 0:
            continue

        r2_key = f"{R2_PREFIX}/{slug}/ep{ep_num:03d}.mp4"
        log(f"    Ep {ep_num:3}/{total_eps}:", end="", flush=True)

        # Get stream
        try:
            sr = requests.get(f"{API_URL}?action=stream&id={drama_id}&episode={ep_num}", timeout=30)
            if sr.status_code != 200:
                log(f" FAIL stream {sr.status_code}")
                time.sleep(0.5)
                continue
            stream_data = sr.json().get("data", {})
        except Exception as e:
            log(f" FAIL stream: {str(e)[:40]}")
            time.sleep(0.5)
            continue

        proxy_url = stream_data.get("proxyUrl", "")
        if not proxy_url:
            log(f" FAIL no proxy URL")
            time.sleep(0.5)
            continue

        # Download
        full_url = f"https://vidrama.asia{proxy_url}" if proxy_url.startswith("/") else proxy_url
        raw_path = drama_temp / f"raw_ep{ep_num:03d}.mp4"
        transcoded_path = drama_temp / f"ep{ep_num:03d}.mp4"

        try:
            resp = requests.get(full_url, timeout=120, stream=True)
            resp.raise_for_status()
            total_bytes = 0
            with open(raw_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1024*1024):
                    f.write(chunk)
                    total_bytes += len(chunk)
            if total_bytes < 1000:
                log(f" FAIL tiny")
                continue
        except Exception as e:
            log(f" FAIL DL: {str(e)[:40]}")
            time.sleep(0.5)
            continue

        raw_mb = raw_path.stat().st_size / 1024 / 1024
        log(f" DL({raw_mb:.1f}MB)", end="", flush=True)

        # Transcode
        if transcode_video(raw_path, transcoded_path):
            upload_path = transcoded_path
        else:
            upload_path = raw_path

        # Upload to R2
        try:
            get_s3().upload_file(str(upload_path), R2_BUCKET, r2_key,
                ExtraArgs={"ContentType": "video/mp4"})
            log(f" R2 OK")
            uploaded.append({
                "number": ep_num,
                "videoUrl": f"{R2_PUBLIC}/{r2_key}",
                "duration": ep.get("duration", 0),
            })
        except Exception as e:
            log(f" R2 FAIL: {str(e)[:40]}")

        # Cleanup
        raw_path.unlink(missing_ok=True)
        transcoded_path.unlink(missing_ok=True)
        time.sleep(0.5)

    shutil.rmtree(drama_temp, ignore_errors=True)
    return uploaded

def register_drama(drama, slug, uploaded_eps):
    """Register drama + episodes in D1."""
    title = drama.get("title", slug)
    desc = drama.get("description", "")
    cover = f"{R2_PUBLIC}/{R2_PREFIX}/{slug}/cover.webp"

    try:
        payload = {
            "title": title,
            "description": desc,
            "cover": cover,
            "provider": "microdrama",
            "totalEpisodes": len(uploaded_eps),
            "isActive": True,
        }
        resp = requests.post(f"{BACKEND_URL}/dramas", json=payload, timeout=15)
        if resp.status_code not in [200, 201]:
            log(f"  Drama API error: {resp.status_code} {resp.text[:80]}")
            return False

        drama_id = resp.json().get("id")
        ep_ok = 0
        for ep in uploaded_eps:
            try:
                er = requests.post(f"{BACKEND_URL}/episodes", json={
                    "dramaId": drama_id,
                    "episodeNumber": ep["number"],
                    "videoUrl": ep["videoUrl"],
                    "duration": ep.get("duration", 0),
                }, timeout=10)
                if er.status_code in [200, 201]:
                    ep_ok += 1
            except:
                pass

        log(f"  REGISTERED: {title} (id={drama_id}, {ep_ok}/{len(uploaded_eps)} eps)")
        return True
    except Exception as e:
        log(f"  Registration error: {e}")
        return False


def main():
    limit = None
    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        if idx + 1 < len(sys.argv):
            limit = int(sys.argv[idx + 1])

    log("=" * 60)
    log("  VIDRAMA MICRODRAMA SCRAPER")
    if limit:
        log(f"  Limit: {limit} dramas")
    log("=" * 60)

    # Discover
    dramas = discover_dramas()
    if not dramas:
        log("  No dramas found!")
        return

    # Save discovery cache
    with open("microdrama_all_dramas.json", "w", encoding="utf-8") as f:
        json.dump(dramas, f, indent=2, ensure_ascii=False)

    # Check R2
    r2_slugs = get_r2_slugs()

    # Check D1
    d1_titles = get_d1_titles()

    # Filter new dramas
    new_dramas = []
    for d in dramas:
        slug = slugify(d.get("title", ""))
        title = d.get("title", "")
        if slug in r2_slugs:
            continue  # Already in R2
        if title in d1_titles:
            continue  # Already in D1
        new_dramas.append(d)

    log(f"\n[4] New dramas to scrape: {len(new_dramas)}")
    if limit:
        new_dramas = new_dramas[:limit]
        log(f"    Limited to: {len(new_dramas)}")

    if not new_dramas:
        log("  Nothing new to scrape!")
        return

    # Create temp dir
    TEMP_DIR.mkdir(exist_ok=True, parents=True)

    # Scrape
    stats = {"ok": 0, "fail": 0, "eps": 0}
    for i, drama in enumerate(new_dramas, 1):
        slug = slugify(drama.get("title", ""))
        title = drama.get("title", slug)

        log(f"\n{'_' * 60}")
        log(f"  [{i}/{len(new_dramas)}] {title}")
        log(f"  Slug: {slug}")

        uploaded = process_drama(drama, slug)

        if uploaded:
            if register_drama(drama, slug, uploaded):
                stats["ok"] += 1
                stats["eps"] += len(uploaded)
            else:
                stats["fail"] += 1
        else:
            stats["fail"] += 1

        time.sleep(1)

    log(f"\n{'=' * 60}")
    log(f"  DONE: {stats['ok']} dramas, {stats['eps']} episodes")
    log(f"  Failed: {stats['fail']}")
    log(f"{'=' * 60}")


if __name__ == "__main__":
    main()
