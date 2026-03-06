#!/usr/bin/env python3
"""
Meloshort Drama Auto-Scraper (Daemon Mode) - FULL METADATA
============================================================
Scrapes dramas from Meloshort via Vidrama's proxy API.
Uploads to R2, registers in backend with isActive=false (pending).

API: https://vidrama.asia/api/meloshort
Actions: list, top, discover, search, detail, episodes, episode_video

Usage:
  python scrape_meloshort.py --probe
  python scrape_meloshort.py --list
  python scrape_meloshort.py --search "keyword"
  python scrape_meloshort.py --scrape <drama_id>
  python scrape_meloshort.py --daemon --target 200
  python scrape_meloshort.py --daemon --target 200 --dry-run
"""

import os, sys, json, time, argparse, re, tempfile, shutil, subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

# === CONFIGURATION ===
BASE_URL = "https://vidrama.asia/api/meloshort"
WORKER_API = "https://api.shortlovers.id/api"

POLL_INTERVAL = 120
SCRAPE_DELAY = 0.3
DRAMA_DELAY = 1
TARGET_DRAMAS = 200
SEGMENT_WORKERS = 4  # parallel .ts segment downloads

R2_ENDPOINT = os.getenv("R2_ENDPOINT")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "kingshort-videos")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Origin": "https://vidrama.asia",
    "Referer": "https://vidrama.asia/",
}

LOG_FILE = Path(__file__).parent / "meloshort_scrape.log"
STATE_FILE = Path(__file__).parent / "meloshort_state.json"


def log(msg, level="INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except:
        pass


def load_state():
    if STATE_FILE.exists():
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"scraped_ids": [], "failed_ids": [], "started_at": None, "last_update": None}


def save_state(state):
    state["last_update"] = datetime.now().isoformat()
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


# === API ===
def api_get(params, timeout=30):
    r = requests.get(BASE_URL, headers=HEADERS, params=params, timeout=timeout)
    r.raise_for_status()
    return r.json()


def check_server_health():
    try:
        data = api_get({"action": "list", "page": 1}, timeout=15)
        dramas = data.get("dramas", [])
        if dramas:
            return True, f"OK ({len(dramas)} dramas on page 1)"
        return False, "No dramas returned"
    except requests.exceptions.HTTPError as e:
        return False, f"HTTP {e.response.status_code}"
    except Exception as e:
        return False, str(e)[:80]


def get_drama_list(page=1):
    data = api_get({"action": "list", "page": page})
    return {
        "dramas": data.get("dramas", []),
        "hasMore": data.get("hasMore", False),
        "page": page,
    }


def get_all_dramas(max_dramas=TARGET_DRAMAS):
    all_dramas = []
    seen_ids = set()
    page = 1
    while len(all_dramas) < max_dramas:
        log(f"Fetching drama list page {page}...")
        try:
            result = get_drama_list(page)
        except Exception as e:
            log(f"Error fetching page {page}: {e}", "WARN")
            break
        dramas = result["dramas"]
        for d in dramas:
            did = d.get("id", "")
            if did and did not in seen_ids:
                seen_ids.add(did)
                all_dramas.append(d)
        log(f"  Page {page}: {len(dramas)} dramas (total: {len(all_dramas)})")
        if not result["hasMore"] or not dramas:
            break
        page += 1
        time.sleep(0.2)
    return all_dramas[:max_dramas]


def get_drama_detail(drama_id):
    return api_get({"action": "detail", "id": drama_id})


def get_episode_video(drama_id, chapter_id):
    data = api_get({"action": "episode_video", "dramaId": drama_id, "chapterId": chapter_id})
    return data


def search_dramas(query, page=1):
    data = api_get({"action": "search", "q": query, "page": page})
    return data.get("dramas", data.get("data", []))


# === R2 & BACKEND ===
def get_r2_client():
    import boto3
    return boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY_ID,
        aws_secret_access_key=R2_SECRET_ACCESS_KEY,
        region_name="auto",
    )


def download_file(url, dest_path, retries=3):
    for attempt in range(retries + 1):
        try:
            r = requests.get(url, headers=HEADERS, stream=True, timeout=120)
            r.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            return dest_path.stat().st_size
        except Exception as e:
            if attempt < retries:
                log(f"      Retry {attempt+1}/{retries}: {e}", "WARN")
                time.sleep(2)
            else:
                raise


def download_hls(m3u8_url, dest_path, retries=2):
    """Download HLS by fetching m3u8, downloading .ts segments, then FFmpeg concat.
    
    FFmpeg's direct m3u8 download hangs on api.meloshort.com's redirect chain,
    but downloading individual segments from v.shortswave.com (GCS) is fast.
    """
    h_dl = {"User-Agent": "Mozilla/5.0", "Referer": "https://api.meloshort.com/"}
    seg_dir = dest_path.parent / f"_segs_{dest_path.stem}"
    
    for attempt in range(retries + 1):
        try:
            seg_dir.mkdir(parents=True, exist_ok=True)
            
            # 1. Fetch m3u8 content (follows redirect)
            r = requests.get(m3u8_url, headers=h_dl, timeout=15)
            r.raise_for_status()
            lines = r.text.strip().split("\n")
            segments = [l.strip() for l in lines if l.strip() and not l.startswith("#")]
            
            if not segments:
                raise RuntimeError("No segments found in m3u8")
            
            # 2. Download .ts segments in parallel (GCS CDN handles concurrency)
            def _dl_seg(args):
                idx, url = args
                sp = seg_dir / f"seg{idx:04d}.ts"
                sr = requests.get(url, stream=True, timeout=60)
                sr.raise_for_status()
                with open(sp, "wb") as f:
                    for chunk in sr.iter_content(chunk_size=65536):
                        f.write(chunk)
                return sp, sp.stat().st_size
            
            seg_files = [None] * len(segments)
            total_bytes = 0
            with ThreadPoolExecutor(max_workers=SEGMENT_WORKERS) as pool:
                futures = {pool.submit(_dl_seg, (i, url)): i for i, url in enumerate(segments)}
                for fut in as_completed(futures):
                    idx = futures[fut]
                    sp, sz = fut.result()
                    seg_files[idx] = sp
                    total_bytes += sz
            
            # 3. FFmpeg concat demux → MP4
            concat_file = seg_dir / "concat.txt"
            with open(concat_file, "w") as f:
                for p in seg_files:
                    f.write(f"file '{str(p).replace(chr(92), '/')}'\n")
            
            cmd = [
                "ffmpeg", "-y", "-f", "concat", "-safe", "0",
                "-i", str(concat_file),
                "-c", "copy", "-movflags", "+faststart",
                str(dest_path),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            # Cleanup segments
            shutil.rmtree(seg_dir, ignore_errors=True)
            
            if result.returncode == 0 and dest_path.exists():
                return dest_path.stat().st_size
            else:
                raise RuntimeError(f"FFmpeg concat exit {result.returncode}")
                
        except Exception as e:
            shutil.rmtree(seg_dir, ignore_errors=True)
            if attempt < retries:
                log(f"      Retry {attempt+1}/{retries}: {e}", "WARN")
                time.sleep(2)
            else:
                raise


def upload_to_r2(local_path, r2_key, content_type="video/mp4"):
    s3 = get_r2_client()
    s3.upload_file(
        str(local_path), R2_BUCKET_NAME, r2_key,
        ExtraArgs={"ContentType": content_type}
    )
    return f"https://stream.shortlovers.id/{r2_key}"


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')[:60]


def extract_metadata(detail, list_item=None):
    """Extract COMPLETE metadata from drama detail."""
    title = detail.get("title") or "Unknown"
    cover = detail.get("cover") or ""
    description = detail.get("description") or detail.get("drama_description") or ""

    # Clean up description
    if description:
        description = re.sub(r'<[^>]+>', '', description).strip()
    if not description or len(description) < 10:
        description = f"Drama pendek Indonesia: {title}"

    # Genres and tags
    genres = detail.get("genres") or detail.get("genre") or []
    if isinstance(genres, str):
        genres = [g.strip() for g in genres.split(",") if g.strip()]
    tag_list = detail.get("tags") or detail.get("tagList") or genres.copy()
    if isinstance(tag_list, str):
        tag_list = [t.strip() for t in tag_list.split(",") if t.strip()]

    # Also try from list item
    if not genres and list_item:
        genres = list_item.get("genres") or list_item.get("genre") or []
        if isinstance(genres, str):
            genres = [g.strip() for g in genres.split(",") if g.strip()]

    # Rating
    rating = 0.0
    heat = detail.get("heat") or detail.get("rating") or detail.get("score") or 0
    if heat:
        try:
            rating = min(10.0, max(0.0, float(heat)))
        except:
            pass

    # Episodes
    episodes = detail.get("episodes") or detail.get("chapters") or []
    total_eps = detail.get("totalEpisodes") or detail.get("total") or detail.get("chapters_count") or len(episodes)
    if isinstance(total_eps, str):
        try:
            total_eps = int(total_eps)
        except:
            total_eps = len(episodes)

    # Country detection
    country = "Indonesia"
    for g in genres:
        g_lower = g.lower() if isinstance(g, str) else ""
        if any(w in g_lower for w in ["china", "tiongkok", "mandarin"]):
            country = "China"
            break
        elif any(w in g_lower for w in ["korea", "korean"]):
            country = "Korea"
            break

    return {
        "title": title,
        "description": description,
        "cover": cover,
        "genres": genres if isinstance(genres, list) else [],
        "tagList": tag_list if isinstance(tag_list, list) else [],
        "rating": rating,
        "totalEpisodes": total_eps,
        "episodes": episodes,
        "country": country,
        "language": "Indonesia",
        "chargeChapters": detail.get("chargeChapters", 0),
        "freeChapters": detail.get("freeChapters", 0),
    }


def register_drama(meta, original_cover=None):
    """Register drama with FULL metadata, isActive=false (PENDING).
    Uses original_cover for initial POST (passes backend HEAD check),
    then PATCHes with R2 cover URL."""
    # Use original cover URL for POST (accessible by backend HEAD check)
    cover_for_post = original_cover or meta["cover"]
    payload = {
        "title": meta["title"],
        "cover": cover_for_post,
        "description": meta["description"],
        "status": "ongoing",
        "country": meta["country"],
        "language": meta["language"],
    }
    if meta["genres"]:
        payload["genres"] = meta["genres"]

    r = requests.post(f"{WORKER_API}/dramas", json=payload, timeout=30)
    if r.status_code not in [200, 201]:
        log(f"  [FAIL] Register failed: {r.status_code} {r.text[:200]}", "ERROR")
        return None

    data = r.json()
    drama_id = data.get("id")

    # PATCH with additional metadata + isActive=false + R2 cover URL
    patch_data = {"isActive": False}
    if meta["cover"] and meta["cover"] != cover_for_post:
        patch_data["cover"] = meta["cover"]  # R2 cover URL
    if meta["tagList"]:
        patch_data["tagList"] = meta["tagList"]
    if meta["rating"] > 0:
        patch_data["rating"] = meta["rating"]

    try:
        requests.patch(f"{WORKER_API}/dramas/{drama_id}", json=patch_data, timeout=10)
    except:
        pass

    log(f"  [OK] Drama registered (PENDING): {drama_id} | {meta['title']}")
    return data


def register_episode(drama_id, ep_num, video_url, title=None, duration=0):
    payload = {
        "dramaId": drama_id,
        "episodeNumber": ep_num,
        "videoUrl": video_url,
        "title": title or f"Episode {ep_num}",
        "duration": duration,
    }
    r = requests.post(f"{WORKER_API}/episodes", json=payload, timeout=30)
    if r.status_code in [200, 201]:
        return r.json()
    else:
        log(f"    [FAIL] Ep {ep_num}: {r.status_code} {r.text[:150]}", "ERROR")
        return None


def register_subtitle(episode_id, language, label, url, is_default=False):
    payload = {
        "language": language,
        "label": label,
        "url": url,
        "isDefault": is_default,
    }
    try:
        r = requests.post(f"{WORKER_API}/episodes/{episode_id}/subtitles", json=payload, timeout=15)
        if r.status_code in [200, 201]:
            return r.json()
        else:
            log(f"      Sub register failed: {r.status_code}", "WARN")
    except Exception as e:
        log(f"      Sub register error: {e}", "WARN")
    return None


def get_language_label(lang_code):
    if not lang_code:
        return "Unknown"
    code = lang_code.lower().split("_")[0].split("-")[0]
    labels = {
        "id": "Indonesian", "ind": "Indonesian", "en": "English",
        "zh": "Chinese", "ja": "Japanese", "ko": "Korean",
        "es": "Spanish", "ms": "Malay", "th": "Thai",
    }
    return labels.get(code, lang_code)


# === SCRAPE ===
def scrape_drama(drama_id, list_item=None, dry_run=False):
    """Full scrape pipeline for one Meloshort drama with COMPLETE metadata."""
    log(f"{'='*50}")
    log(f"Scraping drama: {drama_id}")

    # 1. Get full detail
    try:
        detail = get_drama_detail(drama_id)
    except Exception as e:
        log(f"  [FAIL] Failed to get detail: {e}", "ERROR")
        return None

    meta = extract_metadata(detail, list_item)
    log(f"  Title: {meta['title']}")
    log(f"  Description: {meta['description'][:80]}...")
    log(f"  Genres: {', '.join(meta['genres']) if meta['genres'] else 'N/A'}")
    log(f"  Country: {meta['country']}")
    log(f"  Episodes: {meta['totalEpisodes']} (free: {meta['freeChapters']})")

    episodes = meta["episodes"]
    total_eps = meta["totalEpisodes"] if meta["totalEpisodes"] > 0 else len(episodes)

    if total_eps == 0 or not episodes:
        log(f"  [WARN] No episodes found, skipping", "WARN")
        return None

    if dry_run:
        if episodes:
            ep = episodes[0]
            try:
                vid = get_episode_video(drama_id, ep["id"])
                play_url = vid.get("play_url", "N/A")
                subs = vid.get("subtitles", [])
                dur = vid.get("chapter_duration", 0)
                log(f"  Stream: {play_url[:60]}...")
                log(f"  Duration: {dur}s")
                log(f"  Subtitles: {len(subs)}")
                for s in subs:
                    lang = s.get("language", "?")
                    log(f"    - {lang} ({get_language_label(lang)})")
            except Exception as e:
                log(f"  Stream test failed: {e}", "WARN")
        return {"title": meta["title"], "total_eps": total_eps, "dry_run": True}

    # === FULL SCRAPE ===
    slug = slugify(meta["title"])
    temp_dir = Path(tempfile.gettempdir()) / f"meloshort_{slug}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    # 2. Save original cover URL (accessible, passes backend HEAD check)
    original_cover = meta["cover"]

    # 3. Upload cover to R2
    if meta["cover"]:
        try:
            cover_ext = "webp" if ".webp" in meta["cover"] else "jpg"
            cover_path = temp_dir / f"cover.{cover_ext}"
            download_file(meta["cover"], cover_path)
            r2_key = f"dramas/meloshort/{slug}/cover.{cover_ext}"
            meta["cover"] = upload_to_r2(cover_path, r2_key, f"image/{cover_ext}")
            cover_path.unlink(missing_ok=True)
            log(f"  [OK] Cover uploaded to R2")
        except Exception as e:
            log(f"  [WARN] Cover upload failed: {e}", "WARN")

    # 4. Register drama (PENDING) - use original cover for POST, R2 for PATCH
    drama_data = register_drama(meta, original_cover=original_cover)
    if not drama_data:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return None

    backend_id = drama_data["id"]
    success = 0
    failed = 0
    failed_episodes = []  # Track failed eps for retry

    # 5. Scrape ALL episodes (Vidrama proxy bypasses payment check)
    for ep in episodes:
        ep_num = ep.get("index") or ep.get("chapterIndex") or 0
        ep_id = ep.get("id", "")
        ep_name = ep.get("name", f"E{ep_num:02d}")

        try:
            # Get video URL
            vid_data = get_episode_video(drama_id, ep_id)
            play_url = vid_data.get("play_url", "")
            duration = vid_data.get("chapter_duration", 0)
            subtitles = vid_data.get("subtitles", [])

            if not play_url:
                log(f"    Ep {ep_num}: no play_url", "WARN")
                failed += 1
                continue

            # Download HLS stream via FFmpeg
            ep_path = temp_dir / f"ep{ep_num:03d}.mp4"
            file_size = download_hls(play_url, ep_path)
            size_mb = file_size / (1024 * 1024)

            # Upload to R2
            r2_key = f"dramas/meloshort/{slug}/ep{ep_num:03d}.mp4"
            ep_r2_url = upload_to_r2(ep_path, r2_key)
            ep_path.unlink(missing_ok=True)

            # Register episode in backend
            ep_title = ep_name if ep_name != f"E{ep_num:02d}" else f"Episode {ep_num}"
            ep_result = register_episode(
                drama_id=backend_id,
                ep_num=ep_num,
                video_url=ep_r2_url,
                title=ep_title,
                duration=duration,
            )

            if not ep_result:
                failed += 1
                continue

            ep_backend_id = ep_result.get("id")

            # Handle subtitles: upload to R2 AND register in DB
            for sub in subtitles:
                sub_lang = sub.get("language", "ind-ID")
                sub_url = sub.get("url", "")
                sub_format = sub.get("format", "webvtt")

                if not sub_url:
                    continue

                try:
                    ext = "vtt" if "vtt" in sub_format.lower() or "webvtt" in sub_format.lower() else "srt"
                    sub_path = temp_dir / f"ep{ep_num:03d}_{sub_lang}.{ext}"
                    download_file(sub_url, sub_path)
                    sub_r2_key = f"dramas/meloshort/{slug}/subs/ep{ep_num:03d}_{sub_lang}.{ext}"
                    sub_r2_url = upload_to_r2(sub_path, sub_r2_key, f"text/{ext}")
                    sub_path.unlink(missing_ok=True)

                    # Register subtitle in DB
                    label = get_language_label(sub_lang)
                    is_default = "id" in sub_lang.lower() or "ind" in sub_lang.lower()
                    if ep_backend_id:
                        register_subtitle(ep_backend_id, sub_lang, label, sub_r2_url, is_default)
                    log(f"      Sub ({label}): [OK] R2 + DB")
                except Exception as e:
                    log(f"      Sub ({sub_lang}): [WARN] {e}", "WARN")

            success += 1
            log(f"    Ep {ep_num}/{total_eps}: [OK] ({size_mb:.1f}MB, {duration}s)")
            time.sleep(SCRAPE_DELAY)

        except Exception as e:
            log(f"    Ep {ep_num}: [FAIL] {e}", "ERROR")
            failed += 1
            failed_episodes.append({
                "drama_id": drama_id,
                "backend_id": backend_id,
                "slug": slug,
                "ep_id": ep_id,
                "ep_num": ep_num,
                "ep_name": ep_name,
                "drama_title": meta["title"],
            })

    shutil.rmtree(temp_dir, ignore_errors=True)

    log(f"  DONE: {meta['title']} | OK:{success}/{total_eps} | FAIL:{failed}/{total_eps}")
    return {
        "title": meta["title"],
        "drama_id": str(drama_id),
        "backend_id": backend_id,
        "total_eps": total_eps,
        "success": success,
        "failed": failed,
        "failed_episodes": failed_episodes,
    }


# === DAEMON ===
def daemon_mode(target=TARGET_DRAMAS, dry_run=False):
    log("=" * 60)
    log(f"MELOSHORT DAEMON | Target: {target} dramas | Metadata: FULL")
    log(f"API: {BASE_URL}")
    log(f"State: {STATE_FILE} | Log: {LOG_FILE}")
    log("=" * 60)

    state = load_state()
    if not state.get("started_at"):
        state["started_at"] = datetime.now().isoformat()
        save_state(state)

    scraped = set(state.get("scraped_ids", []))
    failed_ids = set(state.get("failed_ids", []))
    log(f"Resuming: {len(scraped)} scraped, {len(failed_ids)} failed")

    # Phase 1: Check server
    log("\n--- Phase 1: Server check ---")
    healthy, msg = check_server_health()
    if healthy:
        log(f"[OK] Server UP: {msg}")
    else:
        log(f"[WAIT] Down: {msg}. Waiting...")
        while True:
            time.sleep(POLL_INTERVAL)
            healthy, msg = check_server_health()
            if healthy:
                log(f"[OK] Server UP: {msg}")
                break

    # Phase 2: Fetch catalog
    log("\n--- Phase 2: Fetching catalog ---")
    all_dramas = get_all_dramas(max_dramas=target + 50)
    log(f"Found {len(all_dramas)} dramas")

    to_scrape = []
    for d in all_dramas:
        did = d.get("id", "")
        if did and did not in scraped and did not in failed_ids:
            to_scrape.append(d)
    to_scrape = to_scrape[:target - len(scraped)]
    log(f"Will scrape {len(to_scrape)} new (done: {len(scraped)})")

    if not to_scrape:
        log("Nothing to scrape!")
        return

    # Phase 3: Scrape
    log(f"\n--- Phase 3: Scraping ---")
    results = []

    for i, d in enumerate(to_scrape, 1):
        did = d.get("id")
        name = d.get("title", "Unknown")
        log(f"\n[{i}/{len(to_scrape)}] ({len(scraped)+1}/{target}) {name}")

        try:
            result = scrape_drama(did, list_item=d, dry_run=dry_run)
            if result and result.get("success", 0) > 0:
                scraped.add(did)
                state["scraped_ids"] = list(scraped)
                results.append(result)
            elif result and result.get("dry_run"):
                results.append(result)
            else:
                failed_ids.add(did)
                state["failed_ids"] = list(failed_ids)
        except Exception as e:
            log(f"  [CRITICAL] {e}", "ERROR")
            failed_ids.add(did)
            state["failed_ids"] = list(failed_ids)

        save_state(state)

        if len(scraped) >= target:
            log(f"\n>>> TARGET REACHED: {len(scraped)}/{target}")
            break

        time.sleep(DRAMA_DELAY)

        # Health check every 10 dramas
        if i % 10 == 0:
            healthy, msg = check_server_health()
            if not healthy:
                log(f"[WARN] Server down: {msg}", "WARN")
                while True:
                    time.sleep(POLL_INTERVAL)
                    healthy, msg = check_server_health()
                    if healthy:
                        log(f"[OK] Recovered: {msg}")
                        break

    # Collect all failed episodes for retry
    all_failed_eps = []
    for r in results:
        all_failed_eps.extend(r.get("failed_episodes", []))

    # Phase 4: Retry failed episodes
    if all_failed_eps:
        log(f"\n--- Phase 4: Retrying {len(all_failed_eps)} failed episodes ---")
        state["failed_episodes"] = [ep for ep in all_failed_eps]  # save to state
        save_state(state)

        retry_ok = 0
        retry_fail = 0
        for ep_info in all_failed_eps:
            ep_num = ep_info["ep_num"]
            ep_id = ep_info["ep_id"]
            drama_id = ep_info["drama_id"]
            backend_id_ep = ep_info["backend_id"]
            slug = ep_info["slug"]
            title = ep_info["drama_title"]

            log(f"  Retry: {title} Ep {ep_num}")
            try:
                vid_data = get_episode_video(drama_id, ep_id)
                play_url = vid_data.get("play_url", "")
                duration = vid_data.get("chapter_duration", 0)
                subtitles = vid_data.get("subtitles", [])

                if not play_url:
                    log(f"    Still no play_url", "WARN")
                    retry_fail += 1
                    continue

                retry_dir = Path(tempfile.gettempdir()) / f"melo_retry_{slug}"
                retry_dir.mkdir(parents=True, exist_ok=True)
                ep_path = retry_dir / f"ep{ep_num:03d}.mp4"

                file_size = download_hls(play_url, ep_path)
                size_mb = file_size / (1024 * 1024)

                r2_key = f"dramas/meloshort/{slug}/ep{ep_num:03d}.mp4"
                ep_r2_url = upload_to_r2(ep_path, r2_key)
                ep_path.unlink(missing_ok=True)

                ep_title = ep_info.get("ep_name", f"Episode {ep_num}")
                register_episode(
                    drama_id=backend_id_ep,
                    ep_num=ep_num,
                    video_url=ep_r2_url,
                    title=ep_title,
                    duration=duration,
                )

                # Subtitles
                for sub in subtitles:
                    sub_url = sub.get("url", "")
                    sub_lang = sub.get("language", "ind-ID")
                    sub_fmt = sub.get("format", "webvtt")
                    if not sub_url:
                        continue
                    try:
                        ext = "vtt" if "vtt" in sub_fmt.lower() else "srt"
                        sub_path = retry_dir / f"ep{ep_num:03d}_{sub_lang}.{ext}"
                        download_file(sub_url, sub_path)
                        sub_r2 = upload_to_r2(sub_path, f"dramas/meloshort/{slug}/subs/ep{ep_num:03d}_{sub_lang}.{ext}", f"text/{ext}")
                        sub_path.unlink(missing_ok=True)
                    except:
                        pass

                shutil.rmtree(retry_dir, ignore_errors=True)
                retry_ok += 1
                log(f"    [OK] Retry success ({size_mb:.1f}MB)")

            except Exception as e:
                log(f"    [FAIL] Retry failed: {e}", "ERROR")
                retry_fail += 1
            time.sleep(SCRAPE_DELAY)

        log(f"\n  Retry results: OK:{retry_ok} | FAIL:{retry_fail}")
        # Clear retried episodes from state
        if retry_ok > 0:
            state["failed_episodes"] = [ep for ep in all_failed_eps if any(
                ep["ep_id"] == f["ep_id"] for f in all_failed_eps
            )][retry_ok:]  # simplified - just clear all
            state.pop("failed_episodes", None)
            save_state(state)

    # Summary
    log("\n" + "=" * 60)
    log("SCRAPE SUMMARY")
    log("=" * 60)
    log(f"  Target:     {target}")
    log(f"  Scraped:    {len(scraped)}")
    log(f"  Failed:     {len(failed_ids)}")
    log(f"  Eps OK:     {sum(r.get('success', 0) for r in results)}")
    log(f"  Eps Failed: {sum(r.get('failed', 0) for r in results)}")
    if all_failed_eps:
        log(f"  Eps Retry OK:   {retry_ok}")
        log(f"  Eps Retry Fail: {retry_fail}")
    log(f"  Status:     ALL dramas PENDING (isActive=false)")
    log(f"  Next:       Admin panel -> publish")
    log("=" * 60)


def cmd_probe():
    print("=== Probing Meloshort API ===\n")

    healthy, msg = check_server_health()
    print(f"1. Health: {'✅' if healthy else '❌'} {msg}")
    if not healthy:
        print("\n⚠️ Server DOWN. Use --daemon for auto-retry.")
        return

    print("\n2. Drama List")
    result = get_drama_list(1)
    dramas = result["dramas"]
    print(f"   ✅ {len(dramas)} dramas, hasMore: {result['hasMore']}")
    if dramas:
        d = dramas[0]
        print(f"   First: {d.get('title')} (ID: {d.get('id')})")
        did = d.get("id")

        print("\n3. Detail")
        detail = get_drama_detail(did)
        meta = extract_metadata(detail, d)
        print(f"   Title: {meta['title']}")
        print(f"   Description: {meta['description'][:80]}...")
        print(f"   Genres: {meta['genres']}")
        print(f"   Country: {meta['country']}")
        print(f"   Episodes: {meta['totalEpisodes']} (free: {meta['freeChapters']})")

        episodes = meta["episodes"]
        if episodes:
            ep = episodes[0]
            print(f"\n4. Episode Video (ep 1)")
            vid = get_episode_video(did, ep["id"])
            print(f"   play_url: {vid.get('play_url','N/A')[:60]}...")
            print(f"   Duration: {vid.get('chapter_duration', 0)}s")
            subs = vid.get("subtitles", [])
            print(f"   Subtitles: {len(subs)}")
            for s in subs:
                lang = s.get("language", "?")
                print(f"     - {lang} ({get_language_label(lang)}): {s.get('url','')[:60]}...")

    print("\n5. Search ('kurir')")
    try:
        results = search_dramas("kurir")
        print(f"   ✅ {len(results)} results")
        for r in results[:3]:
            print(f"     - {r.get('title', '?')}")
    except Exception as e:
        print(f"   ❌ {e}")


def main():
    parser = argparse.ArgumentParser(description="Meloshort Auto-Scraper (Full Metadata)")
    parser.add_argument("--probe", action="store_true", help="Probe API endpoints")
    parser.add_argument("--list", action="store_true", help="List all dramas")
    parser.add_argument("--search", type=str, help="Search dramas")
    parser.add_argument("--scrape", type=str, help="Scrape single drama by ID")
    parser.add_argument("--daemon", action="store_true", help="Auto-scrape daemon mode")
    parser.add_argument("--target", type=int, default=TARGET_DRAMAS, help="Target number of dramas")
    parser.add_argument("--dry-run", action="store_true", help="Test without downloading")

    args = parser.parse_args()

    if args.probe:
        cmd_probe()
    elif args.list:
        dramas = get_all_dramas(max_dramas=args.target)
        print(f"\nTotal: {len(dramas)}\n")
        for i, d in enumerate(dramas, 1):
            title = d.get("title", "Unknown")
            did = d.get("id")
            print(f"  {i:3d}. [{did}] {title}")
    elif args.search:
        results = search_dramas(args.search)
        print(f"Found {len(results)} results:\n")
        for r in results:
            print(f"  [{r.get('id')}] {r.get('title')}")
    elif args.scrape:
        scrape_drama(args.scrape, dry_run=args.dry_run)
    elif args.daemon:
        daemon_mode(target=args.target, dry_run=args.dry_run)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
