#!/usr/bin/env python3
"""
PARALLEL VIDRAMA SCRAPER - 4 concurrent workers
================================================
Scrapes dramas from Vidrama with 4 parallel episode workers.
Pipeline: Download MP4 → FFmpeg → R2 → DB registration.

Usage:
  python parallel_scrape.py              # Scrape next 8 new dramas
  python parallel_scrape.py --limit 5    # Scrape 5 dramas
  python parallel_scrape.py --workers 6  # Use 6 workers
"""
import requests, json, time, os, re, sys, subprocess, tempfile, shutil, io
from pathlib import Path
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import boto3
from PIL import Image
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except:
    pass

load_dotenv()

# Config
R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET = os.getenv("R2_BUCKET_NAME")
R2_PUBLIC = "https://stream.shortlovers.id"
API_URL = "https://vidrama.asia/api/melolo"
TEMP_DIR = Path(tempfile.gettempdir()) / "vidrama_parallel"
TEMP_DIR.mkdir(exist_ok=True)

NUM_WORKERS = 4
print_lock = Lock()

def get_s3():
    """Each thread gets its own S3 client."""
    return boto3.client("s3", endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY, aws_secret_access_key=R2_SECRET_KEY)

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    return re.sub(r'-+', '-', text).strip('-')

def safe_print(msg):
    with print_lock:
        print(msg, flush=True)

# ─── DISCOVERY (fast) ────────────────────────────────────────

def quick_discover():
    safe_print("  Discovering dramas...")
    all_dramas = {}
    keywords = ["a", "e", "i", "o", "u", "s", "k", "p", "b", "c",
                "d", "m", "r", "n", "t", "l", "g", "h", "j", "w"]
    for kw in keywords:
        try:
            r = requests.get(f"{API_URL}?action=search&keyword={kw}&limit=50&offset=0", timeout=15)
            if r.status_code == 200:
                for d in r.json().get("data", []):
                    did = d.get("id", "")
                    if did and did not in all_dramas:
                        all_dramas[did] = d
            safe_print(f"    '{kw}' → {len(all_dramas)} unique")
            time.sleep(0.3)
        except:
            time.sleep(1)
    safe_print(f"  Total: {len(all_dramas)}")
    return list(all_dramas.values())

def get_existing_titles():
    try:
        r = requests.get("http://localhost:3001/api/dramas?limit=500", timeout=5)
        if r.status_code == 200:
            data = r.json()
            items = data if isinstance(data, list) else data.get("dramas", [])
            return {d["title"] for d in items}
    except:
        pass
    return set()

# ─── EPISODE WORKER ──────────────────────────────────────────

def process_episode(args):
    """Worker function: download → transcode → upload one episode."""
    drama_id, slug, ep_num, total_eps, drama_temp = args
    s3 = get_s3()
    r2_key = f"melolo/{slug}/ep{ep_num:03d}.mp4"
    tag = f"    [{slug}] Ep {ep_num:3}/{total_eps}:"

    # Check if already on R2
    try:
        s3.head_object(Bucket=R2_BUCKET, Key=r2_key)
        safe_print(f"{tag} skip (exists)")
        return {"status": "skip", "ep": ep_num}
    except:
        pass

    # Get stream URL
    try:
        sr = requests.get(f"{API_URL}?action=stream&id={drama_id}&episode={ep_num}", timeout=15)
        if sr.status_code != 200:
            safe_print(f"{tag} ❌ stream {sr.status_code}")
            return {"status": "fail", "ep": ep_num}
        stream_data = sr.json().get("data", {})
    except Exception as e:
        safe_print(f"{tag} ❌ stream err")
        return {"status": "fail", "ep": ep_num}

    proxy_url = stream_data.get("proxyUrl", "")
    if not proxy_url:
        safe_print(f"{tag} ❌ no proxy")
        return {"status": "fail", "ep": ep_num}

    # Download
    full_url = f"https://vidrama.asia{proxy_url}" if proxy_url.startswith("/") else proxy_url
    raw_path = drama_temp / f"raw_ep{ep_num:03d}.mp4"
    out_path = drama_temp / f"ep{ep_num:03d}.mp4"

    try:
        resp = requests.get(full_url, timeout=120, stream=True)
        resp.raise_for_status()
        total = 0
        with open(raw_path, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=1024*1024):
                f.write(chunk)
                total += len(chunk)
        if total < 1000:
            safe_print(f"{tag} ❌ DL tiny")
            return {"status": "fail", "ep": ep_num}
    except Exception as e:
        safe_print(f"{tag} ❌ DL err")
        raw_path.unlink(missing_ok=True)
        return {"status": "fail", "ep": ep_num}

    try:
        raw_mb = raw_path.stat().st_size / 1024 / 1024
    except:
        safe_print(f"{tag} ❌ stat fail")
        return {"status": "fail", "ep": ep_num}

    # Transcode
    try:
        cmd = ["ffmpeg", "-y", "-i", str(raw_path),
               "-c:v", "libx264", "-preset", "fast", "-crf", "28",
               "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "128k", "-ac", "2",
               "-movflags", "+faststart", str(out_path)]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if r.returncode != 0 or not out_path.exists() or out_path.stat().st_size < 1000:
            out_path = raw_path  # fallback to raw
    except:
        out_path = raw_path

    try:
        out_mb = out_path.stat().st_size / 1024 / 1024
    except:
        out_mb = raw_mb
    savings = (1 - out_mb / raw_mb) * 100 if raw_mb > 0 else 0

    # Upload to R2
    try:
        s3.upload_file(str(out_path), R2_BUCKET, r2_key, ExtraArgs={"ContentType": "video/mp4"})
        safe_print(f"{tag} DL({raw_mb:.1f}MB) → FF({out_mb:.1f}MB, {savings:+.0f}%) → R2 ✅")
        result = {"status": "ok", "ep": ep_num, "videoUrl": f"{R2_PUBLIC}/{r2_key}"}
    except Exception as e:
        safe_print(f"{tag} ❌ R2 upload")
        result = {"status": "fail", "ep": ep_num}

    # Cleanup (ignore Windows file lock errors)
    try:
        raw_path.unlink(missing_ok=True)
    except (PermissionError, OSError):
        pass
    try:
        if out_path != raw_path:
            out_path.unlink(missing_ok=True)
    except (PermissionError, OSError):
        pass

    return result

# ─── PROCESS ONE DRAMA ───────────────────────────────────────

def process_drama(drama, slug, workers):
    drama_id = drama["id"]
    
    # Get detail
    try:
        r = requests.get(f"{API_URL}?action=detail&id={drama_id}", timeout=15)
        if r.status_code != 200:
            safe_print(f"  ❌ Detail failed")
            return None
        detail = r.json().get("data", {})
    except:
        safe_print(f"  ❌ Detail error")
        return None

    episodes = detail.get("episodes", [])
    if not episodes:
        safe_print(f"  ❌ No episodes")
        return None

    total_eps = len(episodes)
    safe_print(f"  Episodes: {total_eps}")

    # Merge metadata
    description = detail.get("description", detail.get("desc", drama.get("description", ""))) or "Drama series"
    genres = detail.get("genres", drama.get("genres", []))
    if isinstance(genres, str):
        genres = [g.strip() for g in genres.split(",")]

    # Upload cover (convert any format to proper JPEG)
    cover_url = drama.get("image") or drama.get("poster", "")
    cover_key = f"melolo/{slug}/cover.jpg"
    cover_ok = False
    if cover_url:
        urls = [cover_url]
        if "wsrv" in cover_url:
            from urllib.parse import urlparse, parse_qs
            qs = parse_qs(urlparse(cover_url).query)
            if "url" in qs:
                urls.insert(0, qs["url"][0])
        
        for url in urls:
            try:
                resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
                if resp.status_code == 200 and len(resp.content) > 500:
                    # Convert to JPEG via Pillow (handles HEIC, WebP, PNG, etc.)
                    img = Image.open(io.BytesIO(resp.content))
                    img = img.convert("RGB")
                    if img.width > 800:
                        ratio = 800 / img.width
                        img = img.resize((800, int(img.height * ratio)), Image.LANCZOS)
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG", quality=85, optimize=True)
                    buf.seek(0)
                    jpg_data = buf.getvalue()
                    
                    s3 = get_s3()
                    s3.put_object(Bucket=R2_BUCKET, Key=cover_key, Body=jpg_data, ContentType="image/jpeg")
                    cover_ok = True
                    break
            except:
                continue
    safe_print(f"  Cover: {'✅' if cover_ok else '❌'}")

    # Process episodes in parallel
    drama_temp = TEMP_DIR / slug
    drama_temp.mkdir(exist_ok=True)

    ep_nums = [ep.get("episodeNumber", 0) for ep in episodes if ep.get("episodeNumber", 0) > 0]
    tasks = [(drama_id, slug, ep_num, total_eps, drama_temp) for ep_num in ep_nums]

    uploaded = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(process_episode, t): t[2] for t in tasks}
        for future in as_completed(futures):
            result = future.result()
            if result and result["status"] == "ok":
                uploaded.append(result)

    # Sort by episode number
    uploaded.sort(key=lambda x: x["ep"])
    shutil.rmtree(drama_temp, ignore_errors=True)

    return {
        "title": drama["title"],
        "description": description,
        "genres": genres,
        "totalEpisodes": total_eps,
        "cover_key": cover_key if cover_ok else None,
        "uploaded": uploaded,
    }

# ─── DB REGISTRATION ─────────────────────────────────────────

def infer_genres(title, description):
    """Infer genres from title/description using Indonesian keywords."""
    text = (title + " " + (description or "")).lower()
    genres = {"Drama"}
    
    romance = ["cinta", "nikah", "suami", "istri", "pernikahan", "romansa", "pacar",
               "kekasih", "hati", "jodoh", "dicintai", "digoda", "gadis", "putri",
               "menaklukkan", "dimanja", "bodyguard", "dosen", "idola", "cantik", "ganteng", "tampan"]
    if any(w in text for w in romance): genres.add("Romantis")
    
    action = ["sakti", "petarung", "naga", "kungfu", "bangkit", "kekuatan", "maut", "ahli", "master"]
    if any(w in text for w in action): genres.add("Aksi")
    
    fantasy = ["ajaib", "sihir", "portal", "dunia lain", "dewa", "giok", "kiamat",
               "lahir kembali", "sistem", "reinkarnasi", "supernatural"]
    if any(w in text for w in fantasy): genres.add("Fantasi")
    
    biz = ["ceo", "bisnis", "saham", "kaya", "miskin", "perusahaan", "konglomerat",
           "direktur", "bos", "mafia", "taipan"]
    if any(w in text for w in biz): genres.add("Bisnis")
    
    mystery = ["rahasia", "misteri", "pembunuh", "detektif", "tersembunyi", "terjebak"]
    if any(w in text for w in mystery): genres.add("Misteri")
    
    comedy = ["lucu", "kocak", "komedi", "humor", "galak", "konyol", "manja"]
    if any(w in text for w in comedy): genres.add("Komedi")
    
    family = ["keluarga", "anak", "ibu", "ayah", "adik", "kakak", "orang tua"]
    if any(w in text for w in family): genres.add("Keluarga")
    
    return list(genres)

def register_in_db(info, slug):
    """Register drama + episodes via temp Node.js script (avoids PowerShell escaping)."""
    cover_url = f"{R2_PUBLIC}/{info['cover_key']}" if info["cover_key"] else ""
    
    # Infer genres if Vidrama API returned empty
    genres = info["genres"] if isinstance(info["genres"], list) and info["genres"] else []
    if not genres:
        genres = infer_genres(info["title"], info["description"])
    
    # Write data as JSON file
    reg_data = {
        "title": info["title"],
        "description": (info["description"] or "Drama series")[:500],
        "cover": cover_url,
        "genres": genres,
        "totalEpisodes": info["totalEpisodes"],
        "views": int(time.time()) % 5000 + 1000,
        "episodes": [{"n": e["ep"], "u": e["videoUrl"]} for e in info["uploaded"]],
    }
    
    data_path = Path(r"D:\kingshortid\admin\_reg_data.json")
    script_path = Path(r"D:\kingshortid\admin\_reg_script.js")
    
    data_path.write_text(json.dumps(reg_data, ensure_ascii=False), encoding="utf-8")
    
    script_path.write_text("""
const { PrismaClient } = require('@prisma/client');
const fs = require('fs');
const p = new PrismaClient();
async function main() {
    const data = JSON.parse(fs.readFileSync('_reg_data.json', 'utf8'));
    const drama = await p.drama.create({
        data: {
            title: data.title,
            description: data.description,
            cover: data.cover,
            genres: data.genres,
            totalEpisodes: data.totalEpisodes,
            rating: 4.5,
            views: data.views,
            status: 'ongoing',
            isActive: true,
            country: 'China',
            language: 'Mandarin',
        }
    });
    for (const e of data.episodes) {
        await p.episode.create({
            data: {
                dramaId: drama.id,
                episodeNumber: e.n,
                title: 'Episode ' + e.n,
                videoUrl: e.u,
                duration: 0,
                isActive: true,
            }
        });
    }
    process.stdout.write('OK:' + drama.id + ':' + data.episodes.length);
    await p.$disconnect();
}
main().catch(e => { process.stdout.write('ERR:' + e.message); process.exit(1); });
""", encoding="utf-8")
    
    r = subprocess.run(["node", "_reg_script.js"], capture_output=True, text=True,
                       cwd=r"D:\kingshortid\admin", timeout=120)
    
    # Cleanup
    data_path.unlink(missing_ok=True)
    script_path.unlink(missing_ok=True)
    
    return r.stdout.strip()

# ─── MAIN ────────────────────────────────────────────────────

def main():
    limit = 8
    workers = NUM_WORKERS
    
    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        if idx + 1 < len(sys.argv):
            limit = int(sys.argv[idx + 1])
    if "--workers" in sys.argv:
        idx = sys.argv.index("--workers")
        if idx + 1 < len(sys.argv):
            workers = int(sys.argv[idx + 1])

    print("=" * 60)
    print(f"  PARALLEL VIDRAMA SCRAPER")
    print(f"  Target: {limit} dramas | Workers: {workers}")
    print("=" * 60)

    dramas = quick_discover()
    existing = get_existing_titles()
    new_dramas = [d for d in dramas if d["title"] not in existing]

    print(f"\n  DB: {len(existing)} | New: {len(new_dramas)} | Scraping: {min(limit, len(new_dramas))}\n")

    if not new_dramas:
        print("  Nothing new!")
        return

    new_dramas = new_dramas[:limit]
    stats = {"ok": 0, "fail": 0, "eps": 0}

    for i, drama in enumerate(new_dramas, 1):
        slug = slugify(drama["title"])
        print(f"\n{'─' * 60}")
        print(f"  [{i}/{len(new_dramas)}] {drama['title']}")
        print(f"  Slug: {slug} | Workers: {workers}")

        result = process_drama(drama, slug, workers)

        if result and result["uploaded"]:
            print(f"\n  Uploading: {len(result['uploaded'])}/{result['totalEpisodes']} episodes")
            db_result = register_in_db(result, slug)
            if db_result.startswith("OK"):
                stats["ok"] += 1
                stats["eps"] += len(result["uploaded"])
                print(f"  ✅ Registered: {db_result}")
            else:
                stats["fail"] += 1
                print(f"  ❌ DB error: {db_result}")
        else:
            stats["fail"] += 1
            print(f"  ❌ No episodes uploaded")

        time.sleep(1)

    print(f"\n{'=' * 60}")
    print(f"  DONE: {stats['ok']} dramas, {stats['eps']} episodes")
    print(f"  Failed: {stats['fail']}")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    main()
