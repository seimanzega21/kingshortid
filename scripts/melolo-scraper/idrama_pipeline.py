#!/usr/bin/env python3
"""
IDRAMA PIPELINE — Single Drama Scraper
=======================================
Target: vidrama.asia/provider/idrama
Drama: "Antara Dewa atau Iblis"

Flow:
  1. Inject auth → Load drama detail page
  2. Extract metadata (title, desc, genres, og:image cover)
  3. PROBE Ep1 → Check subtitle type
     - External VTT in response → ABORT
     - No external VTT (embedded) → PROCEED
  4. Loop all episodes: intercept MP4 URL → download → compress → upload R2
  5. Register drama + episodes in DB (isActive=false, draft/pending)
"""

import json, asyncio, re, sys, os, time, subprocess, requests
import boto3, urllib3
from pathlib import Path
from dotenv import load_dotenv
from threading import Lock

# ─────────────────── SETUP ───────────────────
load_dotenv()
sys.stdout.reconfigure(encoding="utf-8")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ─────────────────── CONFIG ───────────────────
VIDRAMA_BASE = "https://vidrama.asia"
PROVIDER     = "idrama"
BACKEND_URL  = "https://api.shortlovers.id/api"
ADMIN_KEY    = "00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14"
R2_PUBLIC    = "https://stream.shortlovers.id"
R2_BUCKET    = os.getenv("R2_BUCKET_NAME", "shortlovers")
R2_PREFIX    = "dramas/idrama"
TEMP_DIR     = Path("C:/tmp/idrama_mp4")
LOG_FILE     = Path(__file__).parent / "idrama_pipeline.log"

# Target drama — hard-coded for single run
TARGET_SLUG = "antara-dewa-atau-iblis"
TARGET_ID   = None  # Will be discovered from page

# Auth data
AUTH_FILE = Path(__file__).parent / "idrama_auth.json"
try:
    AUTH_DATA = json.loads(AUTH_FILE.read_text(encoding="utf-8"))
    SUPABASE_TOKEN = AUTH_DATA.get("access_token", "")
    BROWSER_COOKIES = AUTH_DATA.get("cookies", "")
    SUB_CACHE = AUTH_DATA.get("subscription_cache", {})
except Exception as e:
    print(f"[WARN] Could not load idrama_auth.json: {e}")
    SUPABASE_TOKEN = ""
    BROWSER_COOKIES = ""
    SUB_CACHE = {}

_log_lock = Lock()
_log_fh = open(LOG_FILE, "a", encoding="utf-8")

def log(msg="", end="\n"):
    with _log_lock:
        try: print(msg, end=end, flush=True)
        except: pass
        _log_fh.write(msg + end)
        _log_fh.flush()

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")

# ─────────────────── S3/R2 ───────────────────
_s3 = None
def get_s3():
    global _s3
    if _s3 is None:
        _s3 = boto3.client(
            "s3",
            endpoint_url=os.getenv("R2_ENDPOINT"),
            aws_access_key_id=os.getenv("R2_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("R2_SECRET_ACCESS_KEY"),
            region_name="auto",
        )
    return _s3

# ─────────────────── PLAYWRIGHT BROWSER ───────────────────
from playwright.async_api import async_playwright

_browser = None
_playwright_inst = None
_page = None

async def init_browser():
    """Start Playwright browser with VIP auth injected."""
    global _browser, _playwright_inst, _page
    if _page is not None:
        return

    log("[BROWSER] Launching Chromium...")
    _playwright_inst = await async_playwright().start()
    _browser = await _playwright_inst.chromium.launch(headless=True)
    ctx = await _browser.new_context(
        viewport={"width": 1280, "height": 800},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    )

    # Inject cookies from browser session
    if BROWSER_COOKIES:
        cookie_list = []
        for pair in BROWSER_COOKIES.split(";"):
            pair = pair.strip()
            if "=" in pair:
                name, _, val = pair.partition("=")
                cookie_list.append({
                    "name": name.strip(),
                    "value": val.strip(),
                    "domain": "vidrama.asia",
                    "path": "/",
                })
        try:
            await ctx.add_cookies(cookie_list)
        except Exception as e:
            log(f"[WARN] Cookie injection error: {e}")

    _page = await ctx.new_page()

    # Inject Supabase auth token via localStorage
    log("[BROWSER] Injecting Supabase auth + VIP subscription cache...")
    await _page.goto(f"{VIDRAMA_BASE}/404", timeout=30000)
    if SUPABASE_TOKEN:
        await _page.evaluate(f"""
            localStorage.setItem(
                'sb-gkcnbnlfqdlotnjaizxx-auth-token',
                JSON.stringify({json.dumps(AUTH_DATA)})
            );
            localStorage.setItem('vidrama_subscription_cache', JSON.stringify({json.dumps(SUB_CACHE)}));
        """)
    log("[BROWSER] Auth injected ✅")

async def close_browser():
    global _browser, _playwright_inst, _page
    if _browser:
        await _browser.close()
    if _playwright_inst:
        await _playwright_inst.stop()
    _page = None
    _browser = None
    _playwright_inst = None

# ─────────────────── STEP 1: DISCOVER DRAMA ───────────────────
async def discover_drama_id() -> dict | None:
    """Navigate to provider page to find target drama ID and slug."""
    await init_browser()
    log(f"\n[DISCOVER] Navigating to {VIDRAMA_BASE}/provider/{PROVIDER}...")
    await _page.goto(f"{VIDRAMA_BASE}/provider/{PROVIDER}", timeout=45000)
    await _page.wait_for_timeout(4000)

    # Scroll to load all dramas (lazy load)
    for _ in range(10):
        await _page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await _page.wait_for_timeout(1500)

    # Extract all movie links
    script = """
    () => {
        const links = Array.from(document.querySelectorAll('a[href*="/movie/"]'));
        return links.map(a => {
            const href = a.getAttribute('href') || '';
            const match = href.match(/\\/movie\\/([a-z0-9-]+)--(\\d{10,})/);
            const img = a.querySelector('img');
            return {
                href: href,
                slug: match ? match[1] : '',
                id: match ? match[2] : '',
                title: img ? (img.alt || '') : '',
                cover: img ? (img.src || '') : ''
            };
        }).filter(x => x.slug);
    }
    """
    items = await _page.evaluate(script)
    log(f"[DISCOVER] Found {len(items)} dramas on provider page")

    # Also check direct movie URL pattern
    target = None
    for item in items:
        if TARGET_SLUG in item["slug"] or "antara-dewa" in item["slug"].lower():
            target = item
            log(f"[DISCOVER] ✅ Found target: {item['slug']} (ID: {item['id']})")
            break

    if not target:
        log(f"[DISCOVER] Slug not found in listing. Trying direct search...")
        # Try to find via text search
        all_text = await _page.evaluate("""
            () => Array.from(document.querySelectorAll('a[href*="/movie/"]')).map(a => ({
                href: a.getAttribute('href'),
                text: a.innerText
            }))
        """)
        for item in all_text:
            if "dewa" in (item.get("text") or "").lower() or "iblis" in (item.get("text") or "").lower():
                href = item.get("href", "")
                match = re.search(r"/movie/([a-z0-9-]+)--(\d{10,})", href)
                if match:
                    target = {"slug": match.group(1), "id": match.group(2), "title": item.get("text", ""), "cover": ""}
                    log(f"[DISCOVER] ✅ Found via text: {target['slug']} (ID: {target['id']})")
                    break

    if not target:
        log("[DISCOVER] ❌ Drama not found on provider page! Trying direct URL probe...")
        # Attempt to probe the drama page directly from the screenshot URL structure
        # URL seen: /movie/antara-dewa-atau-iblis--1600006416107?provider=idrama
        test_url = f"{VIDRAMA_BASE}/movie/antara-dewa-atau-iblis--1600006416107?provider={PROVIDER}"
        log(f"[DISCOVER] Trying: {test_url}")
        await _page.goto(test_url, timeout=30000)
        await _page.wait_for_timeout(3000)
        current_url = _page.url
        match = re.search(r"/movie/([a-z0-9-]+)--(\d{10,})", current_url)
        if not match:
            content = await _page.content()
            match = re.search(r"/movie/([a-z0-9-]+)--(\d{10,})", content)
        if match:
            target = {"slug": match.group(1), "id": match.group(2), "title": "Antara Dewa atau Iblis", "cover": ""}
            log(f"[DISCOVER] ✅ Found via direct URL: {target['slug']} (ID: {target['id']})")

    return target

# ─────────────────── STEP 2: SCRAPE METADATA ───────────────────
async def scrape_drama_metadata(drama: dict) -> dict:
    """Extract full metadata from drama detail page."""
    await init_browser()
    url = f"{VIDRAMA_BASE}/movie/{drama['slug']}--{drama['id']}?provider={PROVIDER}"
    log(f"\n[META] Fetching metadata from: {url}")
    await _page.goto(url, wait_until="networkidle", timeout=60000)
    await _page.wait_for_timeout(2000)

    content = await _page.content()

    # High-quality cover from og:image
    og_cover_match = re.search(r'<meta\s+property="og:image"\s+content="([^"]+)"', content)
    if og_cover_match:
        drama["cover_url"] = og_cover_match.group(1)
        log(f"[META] Cover (og:image): {drama['cover_url'][:80]}...")

    # Title from og:title or page title
    og_title = re.search(r'<meta\s+property="og:title"\s+content="([^"]+)"', content)
    if og_title:
        drama["title"] = og_title.group(1).strip()
    if not drama.get("title"):
        drama["title"] = "Antara Dewa atau Iblis"
    log(f"[META] Title: {drama['title']}")

    # Description from og:description or synopsis div
    og_desc = re.search(r'<meta\s+(?:name="description"|property="og:description")\s+content="([^"]+)"', content)
    if og_desc:
        drama["description"] = og_desc.group(1).strip()
    else:
        # Try finding the synopsis block
        synopsis_match = re.search(r'class="[^"]*synopsis[^"]*"[^>]*>(.*?)</div>', content, re.DOTALL)
        if synopsis_match:
            drama["description"] = re.sub(r"<[^>]+>", "", synopsis_match.group(1)).strip()[:800]

    if not drama.get("description"):
        drama["description"] = await _page.evaluate("""
            () => {
                const els = document.querySelectorAll('p, [class*="synopsis"], [class*="desc"]');
                for (const el of els) {
                    const t = el.innerText.trim();
                    if (t.length > 80) return t.substring(0, 800);
                }
                return '';
            }
        """)
    log(f"[META] Description: {drama.get('description','')[:80]}...")

    # Genres
    genres = []
    # Try JSON-LD
    json_ld = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', content, re.DOTALL)
    for jld in json_ld:
        try:
            data = json.loads(jld)
            if isinstance(data, dict) and "genre" in data:
                g = data["genre"]
                genres = [g] if isinstance(g, str) else g
                break
        except: pass

    if not genres:
        genres_raw = await _page.evaluate("""
            () => {
                const tags = Array.from(document.querySelectorAll('a[href*="/genre/"], a[href*="/category/"], [class*="genre"], [class*="tag"]'));
                return [...new Set(tags.map(t => t.innerText.trim()).filter(t => t.length > 1 && t.length < 40))];
            }
        """)
        genres = genres_raw[:5]

    if not genres:
        # fallback from content
        genres = list(set(re.findall(r'"genre"\s*:\s*"([^"]+)"', content)))[:5]

    drama["genres"] = genres if genres else ["Cultivasi", "Drama", "Pertumbuhan Diri"]
    log(f"[META] Genres: {drama['genres']}")

    # Total episodes
    ep_nums = [int(n) for n in re.findall(rf"/watch/{drama['slug']}--{drama['id']}/(\d+)", content)]
    if ep_nums:
        drama["total_episodes"] = max(ep_nums)
    else:
        # Try from API response embedded in page
        ep_count_match = re.search(r'"maxEps"\s*:\s*(\d+)', content)
        if ep_count_match:
            drama["total_episodes"] = int(ep_count_match.group(1))
        else:
            # Count episode buttons/links
            ep_count = await _page.evaluate("""
                () => document.querySelectorAll('a[href*="/watch/"]').length
            """)
            drama["total_episodes"] = ep_count if ep_count > 0 else 50
    log(f"[META] Total episodes detected: {drama['total_episodes']}")

    return drama

# ─────────────────── STEP 3: SUBTITLE PROBE ───────────────────
async def probe_subtitle(drama: dict) -> dict:
    """
    Navigate to watch page for ep 1 and intercept API response.
    Returns: {
        "has_external_vtt": bool,
        "video_url": str,
        "subtitle_url": str,
        "maxEps": int
    }
    """
    await init_browser()
    watch_url = f"{VIDRAMA_BASE}/watch/{drama['slug']}--{drama['id']}/1?provider={PROVIDER}"
    log(f"\n[PROBE] Checking subtitle type on: {watch_url}")

    result = {
        "has_external_vtt": False,
        "video_url": "",
        "subtitle_url": "",
        "maxEps": drama.get("total_episodes", 0),
        "raw_api_data": None,
    }

    captured_responses = []

    async def on_response(resp):
        url = resp.url
        # Intercept any watch API call
        if (
            f"/api/{PROVIDER}/api/watch/" in url
            or "/api/watch/" in url
            or ("watch" in url and "api" in url)
        ):
            try:
                data = await resp.json()
                captured_responses.append({"url": url, "data": data})
                log(f"[PROBE] Intercepted API: {url[:100]}")
            except:
                pass

    _page.on("response", on_response)
    await _page.goto(watch_url, timeout=45000)

    # Wait up to 15s for API to fire
    for _ in range(15):
        if captured_responses:
            break
        await _page.wait_for_timeout(1000)

    _page.remove_listener("response", on_response)

    # Parse captured API data
    for item in captured_responses:
        data = item["data"]
        d = data.get("data", data)  # unwrap if nested
        if isinstance(d, dict):
            if d.get("videoUrl"):
                result["video_url"] = d["videoUrl"]
            if d.get("maxEps"):
                result["maxEps"] = int(d["maxEps"])
            subs = d.get("subtitles", [])
            if subs:
                result["has_external_vtt"] = True
                result["subtitle_url"] = subs[0].get("url", "") if isinstance(subs[0], dict) else str(subs[0])
                log(f"[PROBE] ⚠️  External VTT found: {result['subtitle_url'][:80]}")
            result["raw_api_data"] = d

    # Fallback: check page DOM for subtitle tracks
    if not result["has_external_vtt"]:
        track_url = await _page.evaluate("""
            () => {
                const tracks = document.querySelectorAll('video track, track');
                for (const t of tracks) {
                    if (t.src && t.src.includes('http')) return t.src;
                }
                return null;
            }
        """)
        if track_url:
            result["has_external_vtt"] = True
            result["subtitle_url"] = track_url
            log(f"[PROBE] ⚠️  Subtitle track found in DOM: {track_url[:80]}")

    # Fallback: check for .vtt in page source
    if not result["has_external_vtt"]:
        page_content = await _page.content()
        vtt_urls = re.findall(r'https?://[^\s"\'<>]+\.vtt[^\s"\'<>]*', page_content)
        if vtt_urls:
            result["has_external_vtt"] = True
            result["subtitle_url"] = vtt_urls[0]
            log(f"[PROBE] ⚠️  VTT URL found in page source: {vtt_urls[0][:80]}")

    # Fallback video URL from video element
    if not result["video_url"]:
        result["video_url"] = await _page.evaluate("""
            () => {
                const v = document.querySelector('video');
                if (v) return v.src || v.currentSrc || '';
                return '';
            }
        """)

    if not result["has_external_vtt"]:
        log("[PROBE] ✅ No external VTT found — subtitle appears EMBEDDED in video stream")
    else:
        log(f"[PROBE] ❌ External VTT detected → Pipeline will ABORT per user instruction")

    if result["video_url"]:
        log(f"[PROBE] Video URL: {result['video_url'][:100]}...")
    if result["maxEps"] > 0:
        log(f"[PROBE] maxEps from API: {result['maxEps']}")

    return result

# ─────────────────── STEP 4: GET EPISODE VIDEO URL ───────────────────
async def get_episode_video_url(drama: dict, ep_num: int) -> dict:
    """Intercept the watch API for a specific episode to get MP4 URL."""
    watch_url = f"{VIDRAMA_BASE}/watch/{drama['slug']}--{drama['id']}/{ep_num}?provider={PROVIDER}"
    result = {"video_url": "", "subtitle_url": "", "maxEps": drama.get("total_episodes", 0)}
    captured = []

    async def on_response(resp):
        url = resp.url
        if (
            f"/api/{PROVIDER}/api/watch/" in url
            or "/api/watch/" in url
            or ("watch" in url and "api" in url)
        ):
            try:
                data = await resp.json()
                captured.append(data)
            except:
                pass

    _page.on("response", on_response)
    try:
        await _page.goto(watch_url, timeout=30000)
        for _ in range(12):
            if captured:
                break
            await _page.wait_for_timeout(1000)
    except Exception as e:
        log(f"[EP{ep_num}] Nav error: {str(e)[:50]}")
    _page.remove_listener("response", on_response)

    for data in captured:
        d = data.get("data", data)
        if isinstance(d, dict):
            if d.get("videoUrl"):
                result["video_url"] = d["videoUrl"]
            if d.get("maxEps"):
                result["maxEps"] = int(d["maxEps"])
            subs = d.get("subtitles", [])
            if subs:
                result["subtitle_url"] = subs[0].get("url", "") if isinstance(subs[0], dict) else ""

    # Fallback from video element
    if not result["video_url"]:
        result["video_url"] = await _page.evaluate("""
            () => {
                const v = document.querySelector('video');
                if (!v) return '';
                return v.src || v.currentSrc || '';
            }
        """)

    return result

# ─────────────────── STEP 5: DOWNLOAD / COMPRESS / UPLOAD ───────────────────
def download_mp4(url: str, dest: Path) -> bool:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
        "Referer": "https://vidrama.asia/",
        "Origin": "https://vidrama.asia",
    }
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=headers, timeout=180, stream=True, verify=False)
            resp.raise_for_status()
            total = 0
            with open(dest, "wb") as f:
                for chunk in resp.iter_content(chunk_size=2 * 1024 * 1024):
                    if chunk:
                        f.write(chunk)
                        total += len(chunk)
            if total > 10000:
                return True
            if attempt < 2:
                time.sleep(3)
        except requests.exceptions.HTTPError as e:
            log(f" DLerr:HTTP{e.response.status_code}", end="")
            if attempt < 2:
                time.sleep(3)
        except Exception as e:
            log(f" DLerr:{str(e)[:40]}", end="")
            if attempt < 2:
                time.sleep(3)
    return False

async def compress_mp4_async(src: Path) -> bool:
    """Compress MP4 using FFmpeg via async subprocess (Windows ProactorLoop compatible)."""
    tmp = src.with_name(src.name + ".tmp.mp4")
    cmd = [
        "ffmpeg", "-y", "-i", str(src),
        "-vcodec", "libx264", "-crf", "26", "-preset", "veryfast",
        "-c:a", "aac", "-b:a", "128k",
        "-ar", "44100",
        "-movflags", "+faststart",
        str(tmp),
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=420)
        if proc.returncode == 0 and tmp.exists() and tmp.stat().st_size > 1024:
            src.unlink(missing_ok=True)
            tmp.rename(src)
            return True
        err = stderr.decode("utf-8", "ignore")[:80]
        log(f" FFerr:{err}", end="")
        if tmp.exists():
            tmp.unlink()
        return False
    except asyncio.TimeoutError:
        log(f" FFerr:timeout", end="")
        if tmp.exists():
            tmp.unlink()
        return False
    except Exception as e:
        log(f" FFerr:{str(e)[:40]}", end="")
        if tmp.exists():
            tmp.unlink()
        return False

def upload_mp4(mp4_file: Path, r2_key: str) -> str | None:
    if not mp4_file.exists():
        return None
    try:
        get_s3().upload_file(
            str(mp4_file), R2_BUCKET, r2_key,
            ExtraArgs={"ContentType": "video/mp4"},
        )
        return f"{R2_PUBLIC}/{r2_key}"
    except Exception as e:
        log(f" UPerr:{str(e)[:40]}", end="")
        return None

def upload_cover(cover_url: str, slug: str) -> str | None:
    if not cover_url:
        return None
    try:
        resp = requests.get(cover_url, timeout=20, verify=False,
                            headers={"Referer": "https://vidrama.asia/"})
        if resp.status_code == 200 and len(resp.content) > 500:
            content_type = resp.headers.get("content-type", "image/jpeg")
            ext = "jpg" if "jpeg" in content_type else content_type.split("/")[-1]
            key = f"{R2_PREFIX}/{slug}/cover.{ext}"
            get_s3().put_object(
                Bucket=R2_BUCKET, Key=key,
                Body=resp.content, ContentType=content_type,
            )
            r2_url = f"{R2_PUBLIC}/{key}"
            log(f"[COVER] ✅ Uploaded: {r2_url}")
            return r2_url
    except Exception as e:
        log(f"[COVER] ❌ Error: {e}")
    return None

def check_r2_exists(r2_key: str) -> bool:
    try:
        get_s3().head_object(Bucket=R2_BUCKET, Key=r2_key)
        return True
    except:
        return False

# ─────────────────── STEP 6: REGISTER IN DB ───────────────────
def push_drama_to_db(drama: dict, cover_r2_url: str) -> str | None:
    """Create drama record in DB. Returns drama DB ID or None."""
    payload = {
        "title": drama["title"],
        "description": drama.get("description", ""),
        "status": "Ongoing",
        "provider": "iDrama",
        "isActive": False,
        "tags": drama.get("genres", ["Cultivasi", "Drama"]),
        "cover": cover_r2_url or "",
        "coverUrl": cover_r2_url or "",
        "totalEpisodes": drama.get("total_episodes", 0),
    }
    headers = {"x-api-key": ADMIN_KEY, "Content-Type": "application/json"}
    try:
        resp = requests.post(f"{BACKEND_URL}/dramas", json=payload, headers=headers, timeout=20)
        if resp.status_code in [200, 201]:
            drama_id = resp.json().get("id")
            log(f"[DB] ✅ Drama created: ID={drama_id}")
            # Force isActive=false (some backends override)
            requests.patch(
                f"{BACKEND_URL}/dramas/{drama_id}",
                json={"isActive": False},
                headers=headers,
                timeout=10,
            )
            return drama_id
        log(f"[DB] ❌ Drama create failed {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        log(f"[DB] ❌ Exception: {e}")
    return None

def push_episode_to_db(drama_db_id: str, ep_num: int, video_url: str) -> str | None:
    """Create episode record. Returns episode DB ID or None."""
    payload = {
        "dramaId": drama_db_id,
        "episodeNumber": ep_num,
        "videoUrl": video_url,
        "duration": 0,
    }
    headers = {"x-api-key": ADMIN_KEY, "Content-Type": "application/json"}
    try:
        resp = requests.post(f"{BACKEND_URL}/episodes", json=payload, headers=headers, timeout=15)
        if resp.status_code in [200, 201]:
            return resp.json().get("id")
        log(f"[DB] Ep{ep_num} failed {resp.status_code}: {resp.text[:100]}")
    except Exception as e:
        log(f"[DB] Ep{ep_num} exception: {e}")
    return None

# ─────────────────── EPISODE PROCESSOR (fully async) ───────────────────
async def process_episode(drama: dict, ep_num: int, total_eps: int, drama_temp: Path, drama_db_id: str | None) -> dict | None:
    """Async: fetch URL → download → compress → upload → register in DB."""
    r2_key = f"{R2_PREFIX}/{drama['slug']}/ep{ep_num:03d}.mp4"

    # Skip if already in R2
    if check_r2_exists(r2_key):
        log(f"  Ep {ep_num:3}/{total_eps}: already in R2 ✓")
        r2_url = f"{R2_PUBLIC}/{r2_key}"
        if drama_db_id:
            push_episode_to_db(drama_db_id, ep_num, r2_url)
        return {"number": ep_num, "videoUrl": r2_url}

    log(f"  Ep {ep_num:3}/{total_eps}:", end="")

    # Get video URL via Playwright (runs in same event loop)
    ep_data = await get_episode_video_url(drama, ep_num)
    video_url = ep_data.get("video_url", "")

    if not video_url:
        log(" FAIL(no url)")
        return None

    # Download (blocking I/O — run in thread executor)
    mp4_path = drama_temp / f"ep{ep_num:03d}.mp4"
    log(f" DL...", end="")
    loop = asyncio.get_event_loop()
    dl_ok = await loop.run_in_executor(None, download_mp4, video_url, mp4_path)
    if not dl_ok:
        log(" FAIL(dl)")
        return None

    mb = mp4_path.stat().st_size / 1024 / 1024
    log(f"({mb:.1f}MB)", end="")

    # Compress (async subprocess — Windows ProactorLoop compatible)
    comp_ok = await compress_mp4_async(mp4_path)
    if comp_ok:
        cmb = mp4_path.stat().st_size / 1024 / 1024
        log(f" COMP({cmb:.1f}MB)", end="")

    # Upload to R2
    r2_url = await loop.run_in_executor(None, upload_mp4, mp4_path, r2_key)
    if not r2_url:
        log(" FAIL(upload)")
        return None

    log(" UP✅", end="")
    try:
        mp4_path.unlink()
    except:
        pass

    # Register episode in DB
    if drama_db_id:
        ep_db_id = await loop.run_in_executor(None, push_episode_to_db, drama_db_id, ep_num, r2_url)
        log(f" DB{'✅' if ep_db_id else '⚠️'}")
    else:
        log("")

    return {"number": ep_num, "videoUrl": r2_url, "maxEps": ep_data.get("maxEps", total_eps)}

# ─────────────────── MAIN ───────────────────
async def main():
    log("=" * 65)
    log(f"  🎬 IDRAMA PIPELINE — Antara Dewa atau Iblis")
    log(f"  Provider: {PROVIDER} | R2: {R2_BUCKET}/{R2_PREFIX}")
    log("=" * 65)

    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # ── Step 1: Discover drama ──
    drama = await discover_drama_id()
    if not drama or not drama.get("id"):
        log("\n❌ ABORT: Could not find 'Antara Dewa atau Iblis' on the provider page.")
        log("   Check that vidrama.asia/provider/idrama lists this drama.")
        await close_browser()
        return

    drama_slug = drama["slug"]
    drama_id   = drama["id"]
    log(f"\n✅ Drama found: slug={drama_slug} | id={drama_id}")

    # ── Step 2: Scrape metadata ──
    drama = await scrape_drama_metadata(drama)

    # ── Step 3: Subtitle probe ──
    probe = await probe_subtitle(drama)

    if probe["has_external_vtt"]:
        log("\n" + "=" * 65)
        log("  🚫 PIPELINE ABORTED")
        log("  → External VTT subtitle detected on Episode 1.")
        log(f"  → Subtitle URL: {probe['subtitle_url'][:100]}")
        log("  → Per your instruction: SCRAPING CANCELLED.")
        log("=" * 65)
        await close_browser()
        return

    log("\n✅ Subtitle check passed — No external VTT. Subtitle is EMBEDDED.")

    # Update total episodes from probe
    if probe.get("maxEps", 0) > drama.get("total_episodes", 0):
        drama["total_episodes"] = probe["maxEps"]
    total_eps = drama["total_episodes"]
    log(f"  Total episodes to process: {total_eps}")

    # ── Step 4: Upload cover ──
    cover_r2_url = None
    if drama.get("cover_url"):
        cover_r2_url = upload_cover(drama["cover_url"], drama_slug)
    if not cover_r2_url:
        cover_r2_url = f"{R2_PUBLIC}/{R2_PREFIX}/{drama_slug}/cover.jpg"

    # ── Step 5: Register drama in DB ──
    drama_db_id = push_drama_to_db(drama, cover_r2_url)
    if not drama_db_id:
        log("[WARN] Drama not registered in DB — episodes will still be downloaded but not registered.")

    # ── Step 6: Process episodes ──
    drama_temp = TEMP_DIR / drama_slug
    drama_temp.mkdir(parents=True, exist_ok=True)

    log(f"\n{'=' * 65}")
    log(f"  Processing {total_eps} episodes...")
    log(f"{'=' * 65}")

    # Ep 1 video URL already captured from probe
    success_eps = []
    ep1_video = probe.get("video_url", "")

    ep_num = 1
    while ep_num <= total_eps:
        try:
            # For ep1, override video_url with the one already captured during probe
            if ep_num == 1 and ep1_video:
                r2_key = f"{R2_PREFIX}/{drama_slug}/ep001.mp4"
                if check_r2_exists(r2_key):
                    log(f"  Ep   1/{total_eps}: already in R2 ✓")
                    r2_url = f"{R2_PUBLIC}/{r2_key}"
                    success_eps.append({"number": 1, "videoUrl": r2_url})
                    if drama_db_id:
                        loop = asyncio.get_event_loop()
                        await loop.run_in_executor(None, push_episode_to_db, drama_db_id, 1, r2_url)
                else:
                    log(f"  Ep   1/{total_eps}:", end="")
                    mp4_path = drama_temp / "ep001.mp4"
                    log(f" DL...", end="")
                    loop = asyncio.get_event_loop()
                    dl_ok = await loop.run_in_executor(None, download_mp4, ep1_video, mp4_path)
                    if dl_ok:
                        mb = mp4_path.stat().st_size / 1024 / 1024
                        log(f"({mb:.1f}MB)", end="")
                        comp_ok = await compress_mp4_async(mp4_path)
                        if comp_ok:
                            cmb = mp4_path.stat().st_size / 1024 / 1024
                            log(f" COMP({cmb:.1f}MB)", end="")
                        r2_url = await loop.run_in_executor(None, upload_mp4, mp4_path, r2_key)
                        if r2_url:
                            log(" UP✅", end="")
                            try: mp4_path.unlink()
                            except: pass
                            success_eps.append({"number": 1, "videoUrl": r2_url})
                            if drama_db_id:
                                ep_db_id = await loop.run_in_executor(None, push_episode_to_db, drama_db_id, 1, r2_url)
                                log(f" DB{'✅' if ep_db_id else '⚠️'}")
                            else:
                                log("")
                        else:
                            log(" FAIL(upload)")
                    else:
                        log(" FAIL(dl)")
            else:
                result = await process_episode(drama, ep_num, total_eps, drama_temp, drama_db_id)
                if result:
                    success_eps.append(result)
                    if result.get("maxEps", 0) > total_eps:
                        total_eps = result["maxEps"]
                        log(f"  ✨ Updated total episodes: {total_eps}")

        except KeyboardInterrupt:
            log("\n⚠️  Interrupted by user.")
            break
        except Exception as e:
            log(f"  Ep {ep_num:3}/{total_eps}: Runtime error: {e}")

        ep_num += 1

    # ── Summary ──
    log(f"\n{'=' * 65}")
    log(f"  ✅ PIPELINE COMPLETE")
    log(f"  Drama: {drama['title']}")
    log(f"  Episodes processed: {len(success_eps)}/{total_eps}")
    log(f"  Drama DB ID: {drama_db_id}")
    log(f"  Cover R2: {cover_r2_url}")
    log(f"  Status in DB: Draft/Pending (isActive=false)")
    log(f"  Check Admin Panel → Dramas → filter Pending")
    log("=" * 65)

    await close_browser()


if __name__ == "__main__":
    asyncio.run(main())
