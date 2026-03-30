#!/usr/bin/env python3
"""
IDRAMA PIPELINE v3 — RSC Payload Interceptor
==============================================
iDrama on vidrama.asia uses Next.js RSC (React Server Components).
The video URL comes back as a streaming RSC payload (text/x-component),
NOT as a standard JSON response.

Strategy:
  - Intercept ALL responses including text/x-component RSC payloads
  - Parse RSC chunks for video URLs (mp4, m3u8, signed CDN URLs)
  - Also check the actual <video> element src after load
"""

import json, asyncio, re, sys, os, time, requests
import boto3, urllib3
from pathlib import Path
from dotenv import load_dotenv
from threading import Lock

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

DRAMA_SLUG = "antara-dewa-atau-iblis"
DRAMA_ID   = "1600006416107"

AUTH_FILE = Path(__file__).parent / "idrama_auth.json"
AUTH_DATA = json.loads(AUTH_FILE.read_text(encoding="utf-8"))
SUPABASE_TOKEN = AUTH_DATA.get("access_token", "")
BROWSER_COOKIES = AUTH_DATA.get("cookies", "")
SUB_CACHE = AUTH_DATA.get("subscription_cache", {})

LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
_log_lock = Lock()
_log_fh = open(LOG_FILE, "a", encoding="utf-8")

def log(msg="", end="\n"):
    with _log_lock:
        try: print(msg, end=end, flush=True)
        except: pass
        _log_fh.write(msg + end)
        _log_fh.flush()

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

def check_r2_exists(key: str) -> bool:
    try:
        get_s3().head_object(Bucket=R2_BUCKET, Key=key)
        return True
    except:
        return False

# ─────────────────── BROWSER ───────────────────
from playwright.async_api import async_playwright

_browser = None
_playwright_inst = None
_ctx = None
_page = None

async def init_browser():
    global _browser, _playwright_inst, _ctx, _page
    if _page is not None:
        return

    log("[BROWSER] Launching Chromium...")
    _playwright_inst = await async_playwright().start()
    _browser = await _playwright_inst.chromium.launch(
        headless=True,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-web-security",
        ]
    )
    _ctx = await _browser.new_context(
        viewport={"width": 1280, "height": 800},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        locale="id-ID",
        ignore_https_errors=True,
    )

    # Inject browser cookies from the live session
    if BROWSER_COOKIES:
        cookie_list = []
        for pair in BROWSER_COOKIES.split(";"):
            pair = pair.strip()
            if "=" in pair:
                name, _, val = pair.partition("=")
                cookie_list.append({
                    "name": name.strip(), "value": val.strip(),
                    "domain": "vidrama.asia", "path": "/",
                    "sameSite": "Lax",
                })
        try:
            await _ctx.add_cookies(cookie_list)
            log(f"[BROWSER] Injected {len(cookie_list)} browser cookies")
        except Exception as e:
            log(f"[BROWSER] Cookie error: {e}")

    _page = await _ctx.new_page()

    # Mask automation fingerprint
    await _page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
    """)

    # Inject Supabase auth into localStorage
    await _page.goto(f"{VIDRAMA_BASE}/404", timeout=30000)
    await _page.evaluate(f"""
        localStorage.setItem(
            'sb-gkcnbnlfqdlotnjaizxx-auth-token',
            JSON.stringify({json.dumps(AUTH_DATA)})
        );
        localStorage.setItem(
            'vidrama_subscription_cache',
            JSON.stringify({json.dumps(SUB_CACHE)})
        );
    """)
    log("[BROWSER] Auth injected ✅")

async def close_browser():
    global _browser, _playwright_inst, _page, _ctx
    for obj, method in [(_browser, 'close'), (_playwright_inst, 'stop')]:
        if obj:
            try: await getattr(obj, method)()
            except: pass
    _page = _browser = _playwright_inst = _ctx = None

# ─────────────────── URL EXTRACTION HELPERS ───────────────────
def extract_video_url_from_text(text: str) -> str:
    """Extract first viable streaming video URL from raw text (RSC or HTML)."""
    # Priority: direct mp4 CDN URLs (awscdn, idrama CDN, etc.)
    patterns = [
        r'https?://[^\s"\'\\<>]+\.mp4(?:\?[^\s"\'\\<>]*)?',
        r'https?://[^\s"\'\\<>]+\.m3u8(?:\?[^\s"\'\\<>]*)?',
        r'https?://awscdn\.[^\s"\'\\<>]+',
        r'https?://cdn\.[^\s"\'\\<>]+/[^\s"\'\\<>]+',
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for m in matches:
            # Filter out tracking/analytics URLs
            if any(skip in m for skip in ['analytics', 'beacon', 'gtag', 'pixel', '.js', '.css', '.png', '.jpg', '.svg']):
                continue
            if any(good in m for good in ['.mp4', '.m3u8', 'awscdn', 'auth_key', 'Signature=']):
                return m
    return ""

def extract_json_video_url(data: dict) -> str:
    """Walk dict looking for any videoUrl-like field."""
    if not isinstance(data, dict):
        return ""
    for key in ["videoUrl", "video_url", "url", "streamUrl", "playUrl", "src", "Mopp", "Bcold"]:
        val = data.get(key)
        if val and isinstance(val, str) and "http" in val:
            if any(x in val for x in [".mp4", ".m3u8", "awscdn", "auth_key", "stream"]):
                return val
    # Recurse into nested dicts
    for val in data.values():
        if isinstance(val, dict):
            found = extract_json_video_url(val)
            if found: return found
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, dict):
                    found = extract_json_video_url(item)
                    if found: return found
    return ""

# ─────────────────── WATCH PAGE FETCH ───────────────────
async def get_episode_url(ep_num: int) -> dict:
    """
    Navigate to episode watch page and capture video URL via:
    1. RSC payload (text/x-component streaming chunks)
    2. JSON API responses
    3. Direct video element src
    4. Page source regex scan
    """
    await init_browser()

    result = {
        "video_url": "", "subtitle_url": "",
        "has_external_vtt": False, "maxEps": 0
    }

    watch_url = f"{VIDRAMA_BASE}/watch/{DRAMA_SLUG}--{DRAMA_ID}/{ep_num}?provider={PROVIDER}"
    captured_text = []

    async def on_response(resp):
        url = resp.url
        status = resp.status

        # Skip non-200 and non-content responses
        if status not in [200, 206]:
            return

        ctype = resp.headers.get("content-type", "")

        # Skip static assets
        if any(ext in url for ext in [".js", ".css", ".png", ".jpg", ".svg", ".woff", ".ico", ".webp"]):
            return
        if any(k in url for k in ["analytics", "gtag", "facebook", "clarity", "_vercel"]):
            return

        try:
            # JSON responses
            if "json" in ctype:
                body = await resp.text()
                captured_text.append(body)
                # Try parse
                try:
                    data = json.loads(body)
                    url_found = extract_json_video_url(data)
                    if url_found and not result["video_url"]:
                        result["video_url"] = url_found
                        log(f"  [JSON] Found video URL via {url[:80]}")
                    # Check subtitles
                    txt = body
                    if '"subtitles"' in txt and ('".vtt"' in txt or "vtt" in txt.lower()):
                        result["has_external_vtt"] = True
                        log(f"  [WARN] External VTT detected in JSON response")
                    # maxEps
                    if '"maxEps"' in txt and not result["maxEps"]:
                        m = re.search(r'"maxEps"\s*:\s*(\d+)', txt)
                        if m: result["maxEps"] = int(m.group(1))
                except:
                    pass

            # RSC / text responses (Next.js streaming)
            elif "x-component" in ctype or "text/plain" in ctype or "text/html" in ctype:
                body = await resp.text()
                captured_text.append(body)
                url_found = extract_video_url_from_text(body)
                if url_found and not result["video_url"]:
                    result["video_url"] = url_found
                    log(f"  [RSC] Found video URL in {ctype}: {url_found[:80]}")
                # Check for vtt in RSC body
                if ".vtt" in body and "http" in body:
                    vtt_m = re.search(r'https?://[^\s"\'\\<>]+\.vtt[^\s"\'\\<>]*', body)
                    if vtt_m:
                        result["has_external_vtt"] = True
                        result["subtitle_url"] = vtt_m.group(0)
                        log(f"  [WARN] External VTT in RSC: {vtt_m.group(0)[:80]}")
                if '"maxEps"' in body and not result["maxEps"]:
                    m = re.search(r'"maxEps"\s*:\s*(\d+)', body)
                    if m: result["maxEps"] = int(m.group(1))

            # Direct media URL
            elif any(x in url for x in [".mp4", ".m3u8"]):
                if not result["video_url"]:
                    result["video_url"] = url
                    log(f"  [MEDIA] Direct media URL: {url[:80]}")

        except Exception:
            pass

    _page.on("response", on_response)

    try:
        await _page.goto(watch_url, wait_until="domcontentloaded", timeout=45000)
        # Wait in increments, break early if we got the URL
        for _ in range(25):
            if result["video_url"]:
                break
            await _page.wait_for_timeout(1000)
    except Exception as e:
        log(f"  [NAV] Error ep{ep_num}: {str(e)[:60]}")

    try:
        _page.remove_listener("response", on_response)
    except:
        pass

    # Fallback 1: Read video element
    if not result["video_url"]:
        try:
            vid_src = await _page.evaluate("""
                () => {
                    const v = document.querySelector('video');
                    return v ? (v.currentSrc || v.src || '') : '';
                }
            """)
            if vid_src and "http" in vid_src:
                result["video_url"] = vid_src
                log(f"  [DOM] Video src: {vid_src[:80]}")
        except:
            pass

    # Fallback 2: Scan full page source
    if not result["video_url"]:
        try:
            content = await _page.content()
            url_found = extract_video_url_from_text(content)
            if url_found:
                result["video_url"] = url_found
                log(f"  [SRC] Found in page source: {url_found[:80]}")
        except:
            pass

    # Fallback 3: Use JS to fetch the episode API directly
    if not result["video_url"]:
        try:
            js_result = await _page.evaluate(f"""
                async () => {{
                    try {{
                        const r = await fetch('/api/dotdrama/api/v1/dramas/{DRAMA_ID}/episodes/{ep_num}?lang=id');
                        const d = await r.json();
                        return JSON.stringify(d);
                    }} catch(e) {{ return null; }}
                }}
            """)
            if js_result:
                try:
                    d = json.loads(js_result)
                    url_found = extract_json_video_url(d)
                    if url_found:
                        result["video_url"] = url_found
                        log(f"  [JS-FETCH] Episode API: {url_found[:80]}")
                    log(f"  [JS-FETCH] Response: {js_result[:200]}")
                except:
                    pass
        except:
            pass

    # Check DOM for subtitle tracks
    if not result["has_external_vtt"]:
        try:
            track = await _page.evaluate("""
                () => {
                    const t = document.querySelector('video track, track[kind="subtitles"], track[kind="captions"]');
                    return t ? t.src : null;
                }
            """)
            if track and "http" in track:
                result["has_external_vtt"] = True
                result["subtitle_url"] = track
        except:
            pass

    return result

# ─────────────────── METADATA SCRAPE ───────────────────
async def scrape_metadata() -> dict:
    await init_browser()
    url = f"{VIDRAMA_BASE}/movie/{DRAMA_SLUG}--{DRAMA_ID}?provider={PROVIDER}"
    log(f"[META] Fetching: {url}")

    drama = {"slug": DRAMA_SLUG, "id": DRAMA_ID, "title": "Antara Dewa atau Iblis"}
    meta_captured = []

    async def on_resp(resp):
        if resp.status == 200:
            ctype = resp.headers.get("content-type", "")
            if "json" in ctype or "x-component" in ctype:
                try:
                    body = await resp.text()
                    meta_captured.append(body)
                except: pass

    _page.on("response", on_resp)
    try:
        await _page.goto(url, wait_until="networkidle", timeout=60000)
        await _page.wait_for_timeout(2000)
    except Exception as e:
        log(f"[META] Nav error: {str(e)[:60]}")
    try: _page.remove_listener("response", on_resp)
    except: pass

    content = await _page.content()
    all_text = content + "\n".join(meta_captured)

    # og:image for high-quality cover
    m = re.search(r'<meta\s+property="og:image"\s+content="([^"]+)"', all_text)
    if m:
        drama["cover_url"] = m.group(1)
        log(f"[META] Cover: {drama['cover_url'][:80]}")

    # og:title
    m = re.search(r'<meta\s+property="og:title"\s+content="([^"]+)"', all_text)
    if m: drama["title"] = m.group(1).strip()

    # Description
    m = re.search(r'<meta\s+name="description"\s+content="([^"]+)"', all_text)
    if not m:
        m = re.search(r'<meta\s+property="og:description"\s+content="([^"]+)"', all_text)
    drama["description"] = m.group(1).strip() if m else ""

    if not drama["description"]:
        drama["description"] = await _page.evaluate("""
            () => {
                const sels = ['[class*="synopsis"]', '[class*="desc"]', 'p'];
                for (const s of sels) {
                    const el = document.querySelector(s);
                    if (el && el.innerText && el.innerText.trim().length > 50)
                        return el.innerText.trim().substring(0, 800);
                }
                return '';
            }
        """)
    log(f"[META] Desc: {drama['description'][:70]}...")

    # Genres from page links
    genres = await _page.evaluate("""
        () => [...new Set(
            Array.from(document.querySelectorAll('a[href*="/genre/"], a[href*="/category/"]'))
                .map(e => e.innerText.trim())
                .filter(t => t.length > 1 && t.length < 50)
        )].slice(0, 5)
    """)
    drama["genres"] = genres if genres else ["Cultivasi", "Drama", "Pertumbuhan Diri"]
    log(f"[META] Genres: {drama['genres']}")

    # Episode count
    ep_max = await _page.evaluate(f"""
        () => {{
            const links = document.querySelectorAll('a[href*="/watch/"]');
            let maxN = 0;
            links.forEach(l => {{
                const m = (l.href || '').match(/\\/watch\\/[^/]+\\/(\\d+)/);
                if (m) {{ const n = parseInt(m[1]); if (n > maxN) maxN = n; }}
            }});
            return maxN;
        }}
    """)
    drama["total_episodes"] = ep_max if ep_max > 0 else 0
    log(f"[META] Total episodes from page: {drama['total_episodes']}")
    return drama

# ─────────────────── DOWNLOAD / COMPRESS / UPLOAD ───────────────────
def download_file(url: str, dest: Path) -> bool:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
        "Referer": "https://vidrama.asia/",
        "Origin": "https://vidrama.asia",
    }
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=headers, timeout=300, stream=True, verify=False)
            resp.raise_for_status()
            total = 0
            with open(dest, "wb") as f:
                for chunk in resp.iter_content(chunk_size=2 * 1024 * 1024):
                    if chunk:
                        f.write(chunk)
                        total += len(chunk)
            if total > 10000:
                return True
            log(f" DL_SMALL({total}B)", end="")
        except requests.exceptions.HTTPError as e:
            log(f" DL_HTTP{e.response.status_code}", end="")
        except Exception as e:
            log(f" DL_ERR:{str(e)[:40]}", end="")
        if attempt < 2:
            time.sleep(3 * (attempt + 1))
    return False

async def compress_mp4_async(src: Path) -> bool:
    tmp = src.with_name(src.name + ".compress.mp4")
    cmd = [
        "ffmpeg", "-y", "-i", str(src),
        "-vcodec", "libx264", "-crf", "26", "-preset", "veryfast",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
        "-movflags", "+faststart", str(tmp),
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await asyncio.wait_for(proc.communicate(), timeout=480)
        if proc.returncode == 0 and tmp.exists() and tmp.stat().st_size > 1024:
            src.unlink(missing_ok=True)
            tmp.rename(src)
            return True
        log(f" FF:{stderr.decode('utf-8','ignore')[-80:]}", end="")
        if tmp.exists(): tmp.unlink()
        return False
    except Exception as e:
        log(f" FF_ERR:{str(e)[:30]}", end="")
        if tmp.exists(): tmp.unlink()
        return False

def upload_mp4(mp4_file: Path, r2_key: str) -> str | None:
    if not mp4_file.exists(): return None
    try:
        get_s3().upload_file(str(mp4_file), R2_BUCKET, r2_key, ExtraArgs={"ContentType": "video/mp4"})
        return f"{R2_PUBLIC}/{r2_key}"
    except Exception as e:
        log(f" UP_ERR:{str(e)[:40]}", end="")
        return None

def upload_cover(cover_url: str) -> str | None:
    try:
        resp = requests.get(cover_url, timeout=20, verify=False, headers={"Referer": "https://vidrama.asia/"})
        if resp.status_code == 200 and len(resp.content) > 500:
            ctype = resp.headers.get("content-type", "image/jpeg")
            ext = "jpg" if "jpeg" in ctype else ctype.split("/")[-1].split(";")[0]
            key = f"{R2_PREFIX}/{DRAMA_SLUG}/cover.{ext}"
            get_s3().put_object(Bucket=R2_BUCKET, Key=key, Body=resp.content, ContentType=ctype)
            url = f"{R2_PUBLIC}/{key}"
            log(f"[COVER] ✅ {url}")
            return url
    except Exception as e:
        log(f"[COVER] ❌ {e}")
    return None

# ─────────────────── DB ───────────────────
def push_drama(drama: dict, cover_r2: str) -> str | None:
    hdrs = {"x-api-key": ADMIN_KEY, "Content-Type": "application/json"}
    payload = {
        "title": drama["title"],
        "description": drama.get("description", ""),
        "status": "Ongoing", "provider": "iDrama", "isActive": False,
        "tags": drama.get("genres", ["Drama"]),
        "cover": cover_r2 or "", "coverUrl": cover_r2 or "",
        "totalEpisodes": drama.get("total_episodes", 0),
    }
    try:
        r = requests.post(f"{BACKEND_URL}/dramas", json=payload, headers=hdrs, timeout=20)
        if r.status_code in [200, 201]:
            did = r.json().get("id")
            log(f"[DB] ✅ Drama created: id={did}")
            requests.patch(f"{BACKEND_URL}/dramas/{did}", json={"isActive": False}, headers=hdrs, timeout=10)
            return did
        log(f"[DB] ❌ {r.status_code}: {r.text[:200]}")
    except Exception as e:
        log(f"[DB] ❌ {e}")
    return None

def push_episode(drama_db_id: str, ep_num: int, video_url: str) -> str | None:
    hdrs = {"x-api-key": ADMIN_KEY, "Content-Type": "application/json"}
    try:
        r = requests.post(f"{BACKEND_URL}/episodes",
            json={"dramaId": drama_db_id, "episodeNumber": ep_num, "videoUrl": video_url, "duration": 0},
            headers=hdrs, timeout=15)
        if r.status_code in [200, 201]:
            return r.json().get("id")
        log(f" EP_ERR:{r.status_code}", end="")
    except Exception as e:
        log(f" EP_EX:{str(e)[:30]}", end="")
    return None

# ─────────────────── MAIN ───────────────────
async def main():
    log("=" * 65)
    log(f"  🎬 IDRAMA PIPELINE v3 — {DRAMA_SLUG}")
    log(f"  Provider: {PROVIDER} | Bucket: {R2_BUCKET}/{R2_PREFIX}")
    log(f"  Token expires: {AUTH_DATA.get('expires_at', '?')}")
    log("=" * 65)

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    drama_temp = TEMP_DIR / DRAMA_SLUG
    drama_temp.mkdir(parents=True, exist_ok=True)
    loop = asyncio.get_event_loop()

    # ── Step 1: Metadata ──
    drama = await scrape_metadata()
    log(f"\n📺 {drama['title']} | {drama['genres']} | {drama['total_episodes']} eps")

    # ── Step 2: Probe Ep1 (subtitle check) ──
    log(f"\n[PROBE] Episode 1 subtitle check...")
    ep1_data = await get_episode_url(1)
    log(f"  Video URL: {'✅ found' if ep1_data['video_url'] else '❌ NOT found'}")
    if ep1_data['video_url']:
        log(f"  → {ep1_data['video_url'][:100]}")
    log(f"  External VTT: {'❌ YES → ABORT' if ep1_data['has_external_vtt'] else '✅ NO (embedded)'}")
    if ep1_data.get("maxEps"):
        log(f"  maxEps: {ep1_data['maxEps']}")

    if ep1_data["has_external_vtt"]:
        log("\n🚫 PIPELINE ABORTED — External VTT detected. Scraping cancelled.")
        await close_browser()
        return

    if not ep1_data["video_url"]:
        log("\n⚠️  WARNING: No video URL captured for Ep1. Site may require manual interaction.")
        log("  Continuing anyway — some episodes may fail. Check if VIP session is active.")

    log("\n✅ Subtitle check PASSED. Proceeding with all episodes...")

    # Update episode count from API
    if ep1_data.get("maxEps", 0) > drama["total_episodes"]:
        drama["total_episodes"] = ep1_data["maxEps"]
    if drama["total_episodes"] == 0:
        drama["total_episodes"] = 50  # safe fallback
    total_eps = drama["total_episodes"]
    log(f"  Total episodes: {total_eps}")

    # ── Step 3: Upload cover ──
    cover_r2 = None
    if drama.get("cover_url"):
        cover_r2 = upload_cover(drama["cover_url"])
    if not cover_r2:
        cover_r2 = f"{R2_PUBLIC}/{R2_PREFIX}/{DRAMA_SLUG}/cover.jpg"

    # ── Step 4: Register drama in DB ──
    drama_db_id = push_drama(drama, cover_r2)

    # ── Step 5: Process episodes ──
    log(f"\n{'=' * 65}")
    log(f"  Processing {total_eps} episodes...")
    log(f"{'=' * 65}")

    success_eps = []

    for ep_num in range(1, total_eps + 1):
        try:
            r2_key = f"{R2_PREFIX}/{DRAMA_SLUG}/ep{ep_num:03d}.mp4"

            if check_r2_exists(r2_key):
                log(f"  Ep {ep_num:3}/{total_eps}: R2 ✓ (skip)")
                r2_url = f"{R2_PUBLIC}/{r2_key}"
                success_eps.append({"number": ep_num, "videoUrl": r2_url})
                if drama_db_id:
                    await loop.run_in_executor(None, push_episode, drama_db_id, ep_num, r2_url)
                continue

            log(f"  Ep {ep_num:3}/{total_eps}:", end="")

            # Reuse cached ep1 URL
            if ep_num == 1 and ep1_data.get("video_url"):
                ep_data = ep1_data
                log(f" [cached]", end="")
            else:
                ep_data = await get_episode_url(ep_num)

            video_url = ep_data.get("video_url", "")
            if not video_url:
                log(f" FAIL(no url)")
                continue

            # Download
            mp4_path = drama_temp / f"ep{ep_num:03d}.mp4"
            log(f" DL...", end="")
            dl_ok = await loop.run_in_executor(None, download_file, video_url, mp4_path)
            if not dl_ok:
                log(f" FAIL(dl)")
                continue

            mb = mp4_path.stat().st_size / 1024 / 1024
            log(f"({mb:.1f}MB)", end="")

            # Compress
            comp_ok = await compress_mp4_async(mp4_path)
            if comp_ok:
                cmb = mp4_path.stat().st_size / 1024 / 1024
                log(f" COMP({cmb:.1f}MB)", end="")

            # Upload
            r2_url = await loop.run_in_executor(None, upload_mp4, mp4_path, r2_key)
            if not r2_url:
                log(f" FAIL(upload)")
                continue

            log(f" UP✅", end="")
            try: mp4_path.unlink()
            except: pass

            success_eps.append({"number": ep_num, "videoUrl": r2_url})

            # Register in DB
            if drama_db_id:
                ep_db_id = await loop.run_in_executor(None, push_episode, drama_db_id, ep_num, r2_url)
                log(f" DB{'✅' if ep_db_id else '⚠️'}")
            else:
                log("")

            # Update total eps from API
            if ep_data.get("maxEps", 0) > total_eps:
                total_eps = ep_data["maxEps"]
                log(f"  ✨ Updated total: {total_eps}")

        except KeyboardInterrupt:
            log("\n⚠️  Interrupted.")
            break
        except Exception as e:
            log(f"  Ep {ep_num:3}/{total_eps}: Exception: {e}")

    log(f"\n{'=' * 65}")
    log(f"  ✅ DONE: {len(success_eps)}/{total_eps} episodes processed")
    log(f"  Drama ID: {drama_db_id} | Cover: {cover_r2}")
    log(f"  Admin Panel → Dramas → Pending filter")
    log("=" * 65)

    await close_browser()


if __name__ == "__main__":
    asyncio.run(main())
