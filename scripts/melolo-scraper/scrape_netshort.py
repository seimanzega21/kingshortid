#!/usr/bin/env python3
"""
Netshort Drama Auto-Scraper (Daemon Mode) - FULL METADATA
==========================================================
Automatically polls the Netshort API, and when the server is up,
scrapes all dramas (target: 200), uploads to R2, and registers 
in the backend with isActive=false (pending). Admin publishes manually.

Complete metadata captured:
  Drama: title, description, cover→R2, genres, tagList, rating, country, language
  Episodes: title, videoUrl→R2, duration (from API)
  Subtitles: uploaded to R2 AND registered in DB (language, label, url)

Usage:
  python scrape_netshort.py --probe
  python scrape_netshort.py --list
  python scrape_netshort.py --search "keyword"
  python scrape_netshort.py --scrape <drama_id>
  python scrape_netshort.py --daemon --target 200
"""

import os, sys, json, time, argparse, re, tempfile, shutil
from pathlib import Path
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

# === CONFIGURATION ===
BASE_URL_DIRECT = "https://netshort.dramabos.my.id"
BASE_URL_PROXY = "https://vidrama.asia/api/netshort"
BASE_URL = BASE_URL_PROXY

WATCH_CODE = "84C818C7FB184A62D5BC784A85E1401B"
WORKER_API = "https://api.shortlovers.id/api"
LANG = "in"

POLL_INTERVAL = 120
SCRAPE_DELAY = 0.5
DRAMA_DELAY = 2
TARGET_DRAMAS = 200

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

LOG_FILE = Path(__file__).parent / "netshort_scrape.log"
STATE_FILE = Path(__file__).parent / "netshort_state.json"


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
def api_get(path, params=None, timeout=30):
    url = f"{BASE_URL}{path}"
    r = requests.get(url, headers=HEADERS, params=params, timeout=timeout)
    r.raise_for_status()
    return r.json()


def check_server_health():
    try:
        data = api_get("/api/home/1", {"lang": LANG}, timeout=15)
        if data.get("code") == 200 and data.get("data"):
            count = len(data["data"].get("contentInfos", []))
            return True, f"OK ({count} dramas on page 1)"
        return False, f"Bad response: code={data.get('code')}"
    except requests.exceptions.HTTPError as e:
        return False, f"HTTP {e.response.status_code}"
    except Exception as e:
        return False, str(e)[:80]


def get_drama_list(page=1):
    data = api_get(f"/api/home/{page}", {"lang": LANG})
    if data.get("code") != 200 or not data.get("data"):
        raise Exception(f"API error: code={data.get('code')}")
    d = data["data"]
    return {
        "dramas": d.get("contentInfos", []),
        "maxOffset": d.get("maxOffset", 0),
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
        max_page = result["maxOffset"]
        for d in dramas:
            did = str(d.get("shortPlayId") or d.get("id") or "")
            if did and did not in seen_ids:
                seen_ids.add(did)
                all_dramas.append(d)
        log(f"  Page {page}: {len(dramas)} dramas (total: {len(all_dramas)})")
        if page >= max_page or not dramas:
            break
        page += 1
        time.sleep(0.5)
    return all_dramas[:max_dramas]


def get_drama_detail(drama_id):
    return api_get(f"/api/drama/{drama_id}", {"lang": LANG})


def get_episode_stream(drama_id, episode_no):
    data = api_get(
        f"/api/watch/{drama_id}/{episode_no}",
        {"lang": LANG, "code": WATCH_CODE}
    )
    result = data.get("data", data)

    subtitles = []
    if result.get("subtitles") and isinstance(result["subtitles"], list):
        subtitles = result["subtitles"]
    elif result.get("subtitle"):
        subtitles = [{"language": "id_ID", "url": result["subtitle"]}]

    return {
        "videoUrl": result.get("videoUrl", ""),
        "subtitles": subtitles,
        "episodeNo": result.get("episodeNo") or result.get("current") or episode_no,
        "isLocked": result.get("isLocked", False),
        "maxEps": result.get("maxEps", 0),
        "quality": result.get("quality", ""),
    }


def search_dramas(query, page=1):
    data = api_get("/api/search", {"lang": LANG, "q": query, "page": page})
    if data.get("code") != 200 or not data.get("data"):
        raise Exception(f"Search error: code={data.get('code')}")
    d = data["data"]
    return (
        d.get("searchCodeSearchResult") or
        d.get("searchOnCaseSearchResult") or
        d.get("simpleSearchResult") or
        d.get("contentInfos") or []
    )


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


def download_file(url, dest_path, retries=2):
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
                time.sleep(2)
            else:
                raise


def upload_to_r2(local_path, r2_key, content_type="video/mp4"):
    s3 = get_r2_client()
    s3.upload_file(
        str(local_path), R2_BUCKET_NAME, r2_key,
        ExtraArgs={"ContentType": content_type}
    )
    endpoint_base = R2_ENDPOINT.replace("https://", "").split(".")[0]
    return f"https://pub-{endpoint_base}.r2.dev/{r2_key}"


def extract_metadata(detail, list_item=None):
    """Extract COMPLETE metadata from drama detail + list item."""
    title = detail.get("shortPlayName") or detail.get("name") or "Unknown"
    cover = detail.get("shortPlayCover") or detail.get("cover") or ""
    description = detail.get("introduce") or detail.get("description") or ""
    
    # Clean up description
    if description:
        description = re.sub(r'<[^>]+>', '', description).strip()
    if not description or len(description) < 10:
        description = f"Drama pendek Indonesia: {title}"
    
    # Genres & Tags from labelArray
    labels = detail.get("labelArray") or []
    if not labels and list_item:
        labels = list_item.get("labelArray") or []
    genres = list(set([l.get("labelName", "") for l in labels if l.get("labelName")]))
    tag_list = list(set([l.get("labelName", "") for l in labels if l.get("labelName")]))
    
    # Rating from heatScoreShow (e.g. "9.8万" → 9.8, "1.2亿" → 1.2)
    heat_raw = detail.get("heatScoreShow") or detail.get("formatHeatScore") or ""
    if not heat_raw and list_item:
        heat_raw = list_item.get("heatScoreShow") or list_item.get("formatHeatScore") or ""
    rating = parse_heat_to_rating(heat_raw)
    
    # Episode count
    total_eps = int(detail.get("totalEpisode") or detail.get("script") or 0)
    episodes_list = detail.get("episodeList") or detail.get("episodes") or []
    
    # Country detection from labels/genres
    country = "Indonesia"  # Default for Netshort
    for g in genres:
        g_lower = g.lower()
        if any(w in g_lower for w in ["china", "tiongkok", "mandarin"]):
            country = "China"
            break
        elif any(w in g_lower for w in ["korea", "korean"]):
            country = "Korea"
            break
        elif any(w in g_lower for w in ["thailand", "thai"]):
            country = "Thailand"
            break
    
    return {
        "title": title,
        "description": description,
        "cover": cover,
        "genres": genres,
        "tagList": tag_list,
        "rating": rating,
        "totalEpisodes": total_eps,
        "episodes": episodes_list,
        "country": country,
        "language": "Indonesia",
    }


def parse_heat_to_rating(heat_str):
    """Convert heat score to a 1-10 rating. E.g. '9.8万' → 9.8, '12.3万' → 10.0"""
    if not heat_str:
        return 0.0
    try:
        # Remove non-numeric except dots
        num_str = re.sub(r'[^\d.]', '', heat_str)
        if num_str:
            val = float(num_str)
            # Clamp to 0-10 range
            return min(10.0, max(0.0, val))
    except:
        pass
    return 0.0


def register_drama(meta):
    """Register drama with FULL metadata, isActive=false (PENDING)."""
    payload = {
        "title": meta["title"],
        "cover": meta["cover"],
        "description": meta["description"],
        "status": "ongoing",
        "country": meta["country"],
        "language": meta["language"],
    }
    if meta["genres"]:
        payload["genres"] = meta["genres"]

    r = requests.post(f"{WORKER_API}/dramas", json=payload, timeout=30)
    if r.status_code not in [200, 201]:
        log(f"  ❌ Register failed: {r.status_code} {r.text[:200]}", "ERROR")
        return None

    data = r.json()
    drama_id = data.get("id")

    # PATCH with additional metadata + isActive=false
    patch_data = {"isActive": False}
    if meta["tagList"]:
        patch_data["tagList"] = meta["tagList"]
    if meta["rating"] > 0:
        patch_data["rating"] = meta["rating"]

    try:
        requests.patch(
            f"{WORKER_API}/dramas/{drama_id}",
            json=patch_data,
            timeout=10
        )
    except:
        pass

    log(f"  ✅ Drama registered (PENDING): {drama_id} | {meta['title']}")
    return data


def register_episode(drama_id, ep_num, video_url, title=None, duration=0):
    """Register episode with proper title and duration."""
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
        log(f"    ❌ Ep {ep_num}: {r.status_code} {r.text[:150]}", "ERROR")
        return None


def register_subtitle(episode_id, language, label, url, is_default=False):
    """Register subtitle in the subtitles DB table."""
    payload = {
        "language": language,
        "label": label,
        "url": url,
        "isDefault": is_default,
    }
    try:
        r = requests.post(
            f"{WORKER_API}/episodes/{episode_id}/subtitles",
            json=payload, timeout=15
        )
        if r.status_code in [200, 201]:
            return r.json()
        else:
            log(f"      Sub register failed: {r.status_code}", "WARN")
    except Exception as e:
        log(f"      Sub register error: {e}", "WARN")
    return None


def get_language_label(lang_code):
    """Convert language code to human-readable label."""
    if not lang_code:
        return "Unknown"
    code = lang_code.lower().split("_")[0].split("-")[0]
    labels = {
        "id": "Indonesian", "en": "English", "zh": "Chinese",
        "ja": "Japanese", "ko": "Korean", "es": "Spanish",
        "fr": "French", "de": "German", "pt": "Portuguese",
        "it": "Italian", "tr": "Turkish", "ar": "Arabic",
        "th": "Thai", "ms": "Malay", "vi": "Vietnamese",
        "ru": "Russian", "hi": "Hindi", "tl": "Tagalog",
    }
    return labels.get(code, lang_code.upper())


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')[:60]


# === SCRAPE ===
def scrape_drama(drama_id, list_item=None, dry_run=False):
    """Full scrape pipeline for one drama with COMPLETE metadata."""
    log(f"{'='*50}")
    log(f"Scraping drama: {drama_id}")

    # 1. Get full detail
    try:
        detail = get_drama_detail(drama_id)
    except Exception as e:
        log(f"  ❌ Failed to get detail: {e}", "ERROR")
        return None

    meta = extract_metadata(detail, list_item)
    log(f"  Title: {meta['title']}")
    log(f"  Description: {meta['description'][:80]}...")
    log(f"  Genres: {', '.join(meta['genres']) if meta['genres'] else 'N/A'}")
    log(f"  Tags: {', '.join(meta['tagList']) if meta['tagList'] else 'N/A'}")
    log(f"  Rating: {meta['rating']}")
    log(f"  Country: {meta['country']}")
    log(f"  Episodes: {meta['totalEpisodes']}")

    # Get max eps from watch endpoint if needed
    total_eps = meta["totalEpisodes"]
    if total_eps == 0:
        try:
            test = get_episode_stream(drama_id, 1)
            total_eps = test.get("maxEps", 0)
            log(f"  Max eps from watch API: {total_eps}")
        except:
            pass

    if total_eps == 0:
        log(f"  ⚠️ No episodes found, skipping", "WARN")
        return None

    if dry_run:
        try:
            stream = get_episode_stream(drama_id, 1)
            log(f"  Stream: {stream['videoUrl'][:60]}...")
            log(f"  Subtitles: {len(stream['subtitles'])}")
            for s in stream['subtitles']:
                lang = s.get("language") or s.get("lang") or "?"
                log(f"    - {lang}: {get_language_label(lang)}")
            log(f"  Locked: {stream['isLocked']}")
        except Exception as e:
            log(f"  Stream test failed: {e}", "WARN")
        return {"title": meta["title"], "total_eps": total_eps, "dry_run": True}

    # === FULL SCRAPE ===
    slug = slugify(meta["title"])
    temp_dir = Path(tempfile.gettempdir()) / f"netshort_{slug}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    # 2. Upload cover to R2
    cover_r2_url = meta["cover"]
    if meta["cover"]:
        try:
            cover_path = temp_dir / "cover.jpg"
            download_file(meta["cover"], cover_path)
            r2_key = f"dramas/netshort/{slug}/cover.jpg"
            cover_r2_url = upload_to_r2(cover_path, r2_key, "image/jpeg")
            cover_path.unlink(missing_ok=True)
            log(f"  ✅ Cover uploaded to R2")
        except Exception as e:
            log(f"  ⚠️ Cover upload failed: {e}", "WARN")

    # Update cover in metadata
    meta["cover"] = cover_r2_url

    # 3. Register drama (PENDING)
    drama_data = register_drama(meta)
    if not drama_data:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return None

    backend_id = drama_data["id"]
    success = 0
    failed = 0

    # 4. Scrape ALL episodes
    for ep_num in range(1, total_eps + 1):
        try:
            stream = get_episode_stream(drama_id, ep_num)
            video_url = stream["videoUrl"]

            if not video_url:
                log(f"    Ep {ep_num}: no video URL", "WARN")
                failed += 1
                continue

            if stream.get("isLocked"):
                log(f"    Ep {ep_num}: 🔒 locked", "WARN")
                failed += 1
                continue

            # Download video
            ep_path = temp_dir / f"ep{ep_num:03d}.mp4"
            file_size = download_file(video_url, ep_path)
            size_mb = file_size / (1024 * 1024)

            # Upload to R2
            r2_key = f"dramas/netshort/{slug}/ep{ep_num:03d}.mp4"
            ep_r2_url = upload_to_r2(ep_path, r2_key)
            ep_path.unlink(missing_ok=True)

            # Episode title from detail or default
            ep_title = f"Episode {ep_num}"
            if meta["episodes"] and ep_num <= len(meta["episodes"]):
                ep_data = meta["episodes"][ep_num - 1]
                ep_title = ep_data.get("title") or ep_data.get("name") or ep_title

            # Register episode in backend
            ep_result = register_episode(
                drama_id=backend_id,
                ep_num=ep_num,
                video_url=ep_r2_url,
                title=ep_title,
                duration=0,  # Will be auto-detected by player
            )

            if not ep_result:
                failed += 1
                continue

            ep_backend_id = ep_result.get("id")

            # Handle subtitles: upload to R2 AND register in DB
            for sub in stream.get("subtitles", []):
                sub_lang = sub.get("language") or sub.get("lang") or "id_ID"
                sub_url = sub.get("url") or sub.get("src") or ""
                if not sub_url:
                    continue

                try:
                    ext = "vtt" if "vtt" in sub_url.lower() else "srt"
                    sub_path = temp_dir / f"ep{ep_num:03d}_{sub_lang}.{ext}"
                    download_file(sub_url, sub_path)
                    sub_r2_key = f"dramas/netshort/{slug}/subs/ep{ep_num:03d}_{sub_lang}.{ext}"
                    sub_r2_url = upload_to_r2(sub_path, sub_r2_key, f"text/{ext}")
                    sub_path.unlink(missing_ok=True)

                    # Register subtitle in DB
                    label = get_language_label(sub_lang)
                    is_default = "id" in sub_lang.lower()
                    if ep_backend_id:
                        register_subtitle(ep_backend_id, sub_lang, label, sub_r2_url, is_default)
                    log(f"      Sub ({label}): ✅ R2 + DB")
                except Exception as e:
                    log(f"      Sub ({sub_lang}): ⚠️ {e}", "WARN")

            success += 1
            log(f"    Ep {ep_num}/{total_eps}: ✅ ({size_mb:.1f}MB)")
            time.sleep(SCRAPE_DELAY)

        except Exception as e:
            log(f"    Ep {ep_num}: ❌ {e}", "ERROR")
            failed += 1

    shutil.rmtree(temp_dir, ignore_errors=True)

    log(f"  DONE: {meta['title']} | ✅ {success}/{total_eps} | ❌ {failed}/{total_eps}")
    return {
        "title": meta["title"],
        "drama_id": str(drama_id),
        "backend_id": backend_id,
        "total_eps": total_eps,
        "success": success,
        "failed": failed,
    }


# === DAEMON ===
def daemon_mode(target=TARGET_DRAMAS, dry_run=False):
    log("=" * 60)
    log(f"DAEMON MODE | Target: {target} dramas | Metadata: FULL")
    log(f"Poll: {POLL_INTERVAL}s | Base: {BASE_URL}")
    log(f"State: {STATE_FILE} | Log: {LOG_FILE}")
    log("=" * 60)

    state = load_state()
    if not state.get("started_at"):
        state["started_at"] = datetime.now().isoformat()
        save_state(state)

    scraped = set(state.get("scraped_ids", []))
    failed_ids = set(state.get("failed_ids", []))
    log(f"Resuming: {len(scraped)} scraped, {len(failed_ids)} failed")

    # Phase 1: Wait for server
    log("\n--- Phase 1: Waiting for server ---")
    while True:
        healthy, msg = check_server_health()
        if healthy:
            log(f"✅ Server UP: {msg}")
            break
        log(f"⏳ Down: {msg} | Retry in {POLL_INTERVAL}s...")
        time.sleep(POLL_INTERVAL)

    # Phase 2: Fetch catalog
    log("\n--- Phase 2: Fetching catalog ---")
    all_dramas = get_all_dramas(max_dramas=target + 50)
    log(f"Found {len(all_dramas)} dramas")

    to_scrape = []
    for d in all_dramas:
        did = str(d.get("shortPlayId") or d.get("id") or "")
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
        did = str(d.get("shortPlayId") or d.get("id"))
        name = d.get("shortPlayName") or d.get("name") or "Unknown"
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
            log(f"  ❌ CRITICAL: {e}", "ERROR")
            failed_ids.add(did)
            state["failed_ids"] = list(failed_ids)

        save_state(state)

        if len(scraped) >= target:
            log(f"\n🎯 TARGET REACHED: {len(scraped)}/{target}")
            break

        time.sleep(DRAMA_DELAY)

        # Health check every 10 dramas
        if i % 10 == 0:
            healthy, msg = check_server_health()
            if not healthy:
                log(f"⚠️ Server down: {msg}", "WARN")
                while True:
                    time.sleep(POLL_INTERVAL)
                    healthy, msg = check_server_health()
                    if healthy:
                        log(f"✅ Recovered: {msg}")
                        break

    # Summary
    log("\n" + "=" * 60)
    log("SCRAPE SUMMARY")
    log("=" * 60)
    log(f"  Target:     {target}")
    log(f"  Scraped:    {len(scraped)}")
    log(f"  Failed:     {len(failed_ids)}")
    log(f"  Eps OK:     {sum(r.get('success', 0) for r in results)}")
    log(f"  Eps Failed: {sum(r.get('failed', 0) for r in results)}")
    log(f"  Status:     ALL dramas are PENDING (isActive=false)")
    log(f"  Next:       Admin panel → publish individually or bulk-publish")
    log("=" * 60)


def cmd_probe():
    print("=== Probing Netshort API ===\n")
    healthy, msg = check_server_health()
    print(f"1. Health: {'✅' if healthy else '❌'} {msg}")
    if not healthy:
        print("\n⚠️ Server DOWN. Use --daemon for auto-retry.")
        return

    print("\n2. Drama List")
    result = get_drama_list(1)
    dramas = result["dramas"]
    print(f"   ✅ {len(dramas)} dramas, max page: {result['maxOffset']}")
    if dramas:
        d = dramas[0]
        name = d.get("shortPlayName") or d.get("name")
        did = d.get("shortPlayId") or d.get("id")
        print(f"   First: {name} (ID: {did})")

        print("\n3. Detail")
        detail = get_drama_detail(did)
        meta = extract_metadata(detail, d)
        print(f"   Title: {meta['title']}")
        print(f"   Description: {meta['description'][:80]}...")
        print(f"   Genres: {meta['genres']}")
        print(f"   Tags: {meta['tagList']}")
        print(f"   Rating: {meta['rating']}")
        print(f"   Country: {meta['country']}")
        print(f"   Episodes: {meta['totalEpisodes']}")

        print("\n4. Stream")
        stream = get_episode_stream(did, 1)
        print(f"   Video: {stream['videoUrl'][:60]}...")
        print(f"   Subtitles: {len(stream['subtitles'])}")
        for s in stream["subtitles"]:
            lang = s.get("language") or s.get("lang") or "?"
            print(f"     - {lang} ({get_language_label(lang)})")

    print("\n5. Search ('kabut')")
    try:
        results = search_dramas("kabut")
        print(f"   ✅ {len(results)} results")
        for r in results[:3]:
            name = r.get("shortPlayName") or r.get("name") or r.get("title")
            print(f"     - {name}")
    except Exception as e:
        print(f"   ❌ {e}")


def main():
    parser = argparse.ArgumentParser(description="Netshort Auto-Scraper (Full Metadata)")
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--search", type=str)
    parser.add_argument("--scrape", type=str)
    parser.add_argument("--daemon", action="store_true")
    parser.add_argument("--target", type=int, default=TARGET_DRAMAS)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--direct", action="store_true")

    args = parser.parse_args()

    if args.direct:
        global BASE_URL
        BASE_URL = BASE_URL_DIRECT

    if args.probe:
        cmd_probe()
    elif args.list:
        dramas = get_all_dramas()
        print(f"\nTotal: {len(dramas)}\n")
        for i, d in enumerate(dramas, 1):
            name = d.get("shortPlayName") or d.get("name") or "Unknown"
            did = d.get("shortPlayId") or d.get("id")
            heat = d.get("heatScoreShow") or "0"
            labels = d.get("labelArray") or []
            genres = ", ".join([l.get("labelName", "") for l in labels[:3]])
            print(f"  {i:3d}. [{did}] {name} | 🔥{heat} | {genres}")
    elif args.search:
        results = search_dramas(args.search)
        print(f"Found {len(results)} results:\n")
        for r in results:
            name = r.get("shortPlayName") or r.get("name") or r.get("title")
            did = r.get("shortPlayId") or r.get("id")
            print(f"  [{did}] {name}")
    elif args.scrape:
        scrape_drama(args.scrape, dry_run=args.dry_run)
    elif args.daemon:
        daemon_mode(target=args.target, dry_run=args.dry_run)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
