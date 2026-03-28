#!/usr/bin/env python3
"""
NETSHORT PIPELINE SCRAPER v1 - DIRECT MP4 UPLOAD
=================================================
Pipeline:
1. Fetch drama list from vidrama.asia/provider/netshort
2. Fetch episode count and metadata
3. Download direct MP4 chunks from awscdn.netshort.com
4. Upload MP4 directly to Cloudflare R2 (no HLS conversion per user request)
5. Register in DB with `isActive: false` (pending review)
"""
import requests, json, time, os, re, sys, subprocess, boto3
from pathlib import Path
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

load_dotenv()
sys.stdout.reconfigure(encoding="utf-8")

# ──────────────────── CONFIG ────────────────────
VIDRAMA_BASE  = "https://vidrama.asia"
BACKEND_URL   = "https://api.shortlovers.id/api"
R2_PUBLIC     = "https://stream.shortlovers.id"
R2_BUCKET     = os.getenv("R2_BUCKET_NAME") or "shortlovers"
R2_PREFIX     = "dramas/netshort"
TEMP_DIR      = Path("C:/tmp/netshort_mp4")
LOG_FILE      = Path(__file__).parent / "netshort_pipeline.log"
DRAMA_LIMIT   = 50
EP_WORKERS    = 2

# We need the tokens injected earlier (Netshort probe v3)
try:
    AUTH_DATA = json.loads(Path("netshort_auth.json").read_text())
    SUPABASE_TOKEN = AUTH_DATA.get("access_token", "")
except:
    SUPABASE_TOKEN = "" # Will use next-action approach without auth if possible

# Magic token found from probe for triggering server actions
NEXT_ACTION = "40c1405810e1d492d36c686b19fdd772f47beba84f"

_log_lock = Lock()
_log_fh = open(LOG_FILE, "a", encoding="utf-8")

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
            region_name="auto"
        )
    return _s3

# ──────────────────── API CALLS ────────────────────
def extract_dramas_from_provider_page() -> list:
    """Fetch Netshort page and parse HTML/RSC to get basic drama info."""
    log("[API] Fetching Netshort frontpage...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
        "RSC": "1",
        "Next-Url": "/provider/netshort"
    }
    try:
        r = requests.get(f"{VIDRAMA_BASE}/provider/netshort", headers=headers, timeout=20)
        text = r.text
        
        # Regex to find links to movies
        # Format: "/movie/title-slug--2034897075744800770"
        matches = re.findall(r'"/movie/([a-z0-9-]+)--(\d{15,})"', text)
        
        # Also try to extract titles and covers roughly
        titles = re.findall(r'"title"\s*:\s*"([^"]+)"', text)
        covers = re.findall(r'"cover_url"\s*:\s*"([^"]+)"', text)
        
        dramas = []
        seen = set()
        for idx, (slug, did) in enumerate(matches):
            if did in seen: continue
            seen.add(did)
            
            title = titles[idx] if idx < len(titles) else slug.replace("-", " ").title()
            cover = covers[idx] if idx < len(covers) else ""
            
            dramas.append({
                "id": did,
                "slug": slug,
                "title": title,
                "cover_url": cover
            })
            if len(dramas) >= DRAMA_LIMIT: break
            
        log(f"  -> Found {len(dramas)} unique dramas")
        return dramas
    except Exception as e:
        log(f"  ❌ Error fetching drama list: {e}")
        return []

def extract_drama_metadata(drama: dict) -> dict:
    """Fetch drama page to get full description, genres, and exact episode count."""
    log(f"  [API] Fetching metadata for '{drama['title']}'...")
    headers = {
        "User-Agent": "Mozilla/5.0",
        "RSC": "1",
        "Next-Url": f"/movie/{drama['slug']}--{drama['id']}?provider=netshort"
    }
    try:
        r = requests.get(f"{VIDRAMA_BASE}/movie/{drama['slug']}--{drama['id']}?provider=netshort", headers=headers, timeout=15)
        text = r.text
        
        # Find description
        desc = ""
        desc_matches = re.findall(r'"description"\s*:\s*"([^"]+)"', text)
        if (desc_matches): desc = desc_matches[-1] # Usually the longest/last one
        
        # Find total episodes
        total_episodes = 0
        ep_matches = re.findall(r'"total_episodes"\s*:\s*(\d+)', text)
        if not ep_matches:
            ep_matches = re.findall(r'"episode_count"\s*:\s*(\d+)', text)
            
        if ep_matches:
            total_episodes = int(ep_matches[0])
        else:
            # Try to find max episode number from links
            ep_nums = [int(n) for n in re.findall(rf'/watch/{drama["slug"]}--{drama["id"]}/(\d+)', text)]
            if ep_nums: total_episodes = max(ep_nums)
            else: total_episodes = 50 # Fallback default
            
        # Find genres
        genres = list(set(re.findall(r'"genre"\s*:\s*"([^"]+)"', text)))
        if not genres:
            genres = list(set(re.findall(r'"category_name"\s*:\s*"([^"]+)"', text)))
            
        return {
            **drama,
            "description": desc,
            "total_episodes": total_episodes,
            "genres": genres[:3] if genres else ["Drama", "Romantis"]
        }
    except Exception as e:
        log(f"  ❌ Metadata error: {e}")
from playwright.async_api import async_playwright
import asyncio

# Need a global browser context instance to reuse for speed
_browser = None
_playwright = None
_page = None

async def init_browser():
    global _browser, _playwright, _page
    if _page is not None: return
    
    _playwright = await async_playwright().start()
    _browser = await _playwright.chromium.launch(headless=True)
    ctx = await _browser.new_context(
        viewport={"width": 1280, "height": 800},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36"
    )
    _page = await ctx.new_page()
    
    # Inject auth token to bypass Cloudflare login
    log("  [BROWSER] Initializing browser & injecting auth...")
    await _page.goto("https://vidrama.asia/404", timeout=30000)
    if SUPABASE_TOKEN:
        await _page.evaluate(f"""
            localStorage.setItem(
                'sb-gkcnbnlfqdlotnjaizxx-auth-token',
                JSON.stringify({json.dumps(AUTH_DATA)})
            );
            localStorage.setItem('vidrama_subscription_cache', JSON.stringify({{
                "userId": "6f3e5c15-a21c-4d10-b86c-e88170e7b72d",
                "status": "vip",
                "tier": "vip",
                "timestamp": Date.now()
            }}));
        """)

async def get_episode_video_url_async(drama_id: str, slug: str, ep_num: int) -> str:
    """Use Playwright to get the Netshort AWS CDN MP4 URL."""
    try:
        await init_browser()
        watch_url = f"{VIDRAMA_BASE}/watch/{slug}--{drama_id}/{ep_num}?provider=netshort"
        
        # Intercept response to find video URL directly from network
        found_url = ""
        def handle_response(response):
            nonlocal found_url
            if "awscdn.netshort.com" in response.url or ".mp4" in response.url.lower():
                found_url = response.url
                
        _page.on("response", handle_response)
        
        await _page.goto(watch_url, timeout=30000)
        await _page.wait_for_timeout(4000) # Wait for video player to initialize
        
        _page.remove_listener("response", handle_response)
        
        if found_url:
            return found_url
            
        # Fallback to checking DOM directly
        video_src = await _page.evaluate("() => { const v = document.querySelector('video'); return v?.src || v?.currentSrc; }")
        if video_src and video_src.startswith("http"):
            return video_src
            
    except Exception as e:
        log(f"  ❌ Playwright error fetching Ep {ep_num}: {str(e)[:50]}")
    
    return ""

def get_episode_video_url(drama_id: str, slug: str, ep_num: int) -> str:
    """Sync wrapper for async Playwright function."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(get_episode_video_url_async(drama_id, slug, ep_num))

import base64

async def _download_mp4_async(url: str, dest: Path) -> bool:
    try:
        await init_browser()
        dl_page = await _browser.contexts[0].new_page()
        
        # Navigate to vidrama so we have the right Origin/Referer for fetch
        await dl_page.goto("https://vidrama.asia/404", timeout=30000)
        
        # Fetch the video using JS (bypasses UI download limitations)
        log("  [FETCHing MP4...]", end="")
        script = f"""
        async () => {{
            const resp = await fetch("{url}");
            if (!resp.ok) throw new Error("HTTP " + resp.status);
            const blob = await resp.blob();
            const buffer = await blob.arrayBuffer();
            const bytes = new Uint8Array(buffer);
            let binary = '';
            // Process in chunks to avoid max call stack size exceeded
            const chunkSize = 8192;
            for (let i = 0; i < bytes.length; i += chunkSize) {{
                binary += String.fromCharCode.apply(null, bytes.subarray(i, i + chunkSize));
            }}
            return btoa(binary);
        }}
        """
        try:
            # For large files, evaluate might hit memory limits, but these are small 1-3 min shorts (~5-15MB)
            b64_data = await dl_page.evaluate(script)
            
            with open(dest, "wb") as f:
                f.write(base64.b64decode(b64_data))
                
            await dl_page.close()
            mb = dest.stat().st_size / 1024 / 1024
            return mb > 0.5 # Successful if larger than 0.5MB
        except Exception as e:
            log(f"  JS DLerr:{str(e)[:40]}", end="")
            await dl_page.close()
            return False
            
    except Exception as e:
        log(f"  DLerr:{str(e)[:40]}", end="")
        return False

def download_mp4(url: str, dest: Path) -> bool:
    """Download MP4 directly to disk using Playwright (bypasses CF blocks)."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(_download_mp4_async(url, dest))

def upload_mp4(mp4_file: Path, r2_key: str) -> str | None:
    """Upload directly as MP4."""
    if not mp4_file.exists(): return None
    try:
        get_s3().upload_file(str(mp4_file), R2_BUCKET, r2_key,
                             ExtraArgs={"ContentType": "video/mp4"})
        return f"{R2_PUBLIC}/{r2_key}"
    except Exception as e:
        log(f" UPerr:{str(e)[:30]}", end="")
        return None

def upload_cover(cover_url: str, slug: str) -> bool:
    if not cover_url: return False
    try:
        resp = requests.get(cover_url, timeout=15)
        if resp.status_code == 200 and len(resp.content) > 100:
            get_s3().put_object(Bucket=R2_BUCKET,
                                Key=f"{R2_PREFIX}/{slug}/cover.webp",
                                Body=resp.content,
                                ContentType=resp.headers.get("content-type", "image/webp"))
            return True
    except: pass
    return False

# ──────────────────── WORKERS ────────────────────
def process_episode(drama_id: str, slug: str, ep_num: int, drama_temp: Path, total_eps: int) -> dict | None:
    """Process single episode: fetch url → download MP4 → upload MP4 to R2."""
    r2_key = f"{R2_PREFIX}/{slug}/ep{ep_num:03d}.mp4"
    
    # Check if exists in R2
    try:
        get_s3().head_object(Bucket=R2_BUCKET, Key=r2_key)
        log(f"    Ep {ep_num:3}/{total_eps}: already in R2")
        return {"number": ep_num, "videoUrl": f"{R2_PUBLIC}/{r2_key}", "duration": 0}
    except: pass
    
    log(f"    Ep {ep_num:3}/{total_eps}:", end="")
    
    # 1. Get CDN URL
    video_url = get_episode_video_url(drama_id, slug, ep_num)
    if not video_url:
        log(f" FAIL (no url)"); return None
        
    log(f"    URL: {video_url[:120]}...", end="")

    # 2. Download MP4
    mp4_path = drama_temp / f"ep{ep_num:03d}.mp4"
    if not download_mp4(video_url, mp4_path):
        log(f" FAIL (dl)"); return None
        
    mb = mp4_path.stat().st_size / 1024 / 1024
    log(f" DL({mb:.1f}MB)", end="")
    
    # 3. Upload to R2
    r2_url = upload_mp4(mp4_path, r2_key)
    if not r2_url:
        log(f" FAIL(upload)"); return None
        
    log(f" UP(OK)")
    
    # 4. Cleanup temp file
    try: mp4_path.unlink()
    except: pass
    
    return {"number": ep_num, "videoUrl": r2_url, "duration": 0}

def push_to_backend(drama_data: dict, episodes: list) -> bool:
    """Push to Kingshort backend. IMPORTANT: isActive: false"""
    log("  [DB] Pushing to Backend Admin API...")
    admin_key = os.getenv("ADMIN_API_KEY")
    try:
        payload = {
            "title": drama_data["title"],
            "description": drama_data.get("description", "") or "-",
            "status": "Ongoing",
            "provider": "Netshort", # Track source
            "isActive": False,      # <--- User requested pending state
            "tags": drama_data.get("genres", ["Drama", "Romance"]),
            "coverUrl": f"{R2_PUBLIC}/{R2_PREFIX}/{drama_data['slug']}/cover.webp",
            "episodes": sorted(episodes, key=lambda e: e["number"])
        }
        resp = requests.post(f"{BACKEND_URL}/admin/dramas",
                             json=payload, headers={"X-Admin-Key": admin_key}, timeout=20)
        
        if resp.status_code in [200, 201]:
            log(f"  ✅ Saved ID {resp.json().get('id', '?')} to DB (Pending)")
            return True
        else:
            log(f"  ❌ DB Error {resp.status_code}: {resp.text}")
            return False
    except Exception as e:
        log(f"  ❌ Post exception: {e}")
        return False

# ──────────────────── MAIN LOOP ────────────────────
def main():
    log("=" * 60)
    log(f"🚀 NETSHORT MP4 SCRAPER v1 (R2 Prefix: {R2_PREFIX})")
    log("=" * 60)
    
    # Setup temp storage
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Fetch Dramas
    dramas = extract_dramas_from_provider_page()
    if not dramas:
        log("No dramas found. Exiting.")
        return
        
    for i, base_drama in enumerate(dramas, 1):
        log(f"\n[{i}/{len(dramas)}] 🎬 {base_drama['title']} ({base_drama['id']})")
        
        # 2. Get full metadata
        drama = extract_drama_metadata(base_drama)
        total_eps = drama["total_episodes"]
        if total_eps < 1: total_eps = 50 # Fallback
        
        log(f"  Info: {total_eps} eps | {drama.get('genres')} | {drama.get('description')[:50]}...")
        
        # Determine if already injected?
        drama_temp = TEMP_DIR / drama["slug"]
        drama_temp.mkdir(parents=True, exist_ok=True)
        
        # Upload cover
        upload_cover(drama["cover_url"], drama["slug"])
        
        # 3. Process Episodes in Parallel (2 at a time)
        success_eps = []
        with ThreadPoolExecutor(max_workers=EP_WORKERS) as executor:
            futures = {
                executor.submit(process_episode, drama["id"], drama["slug"], ep_num, drama_temp, total_eps): ep_num
                for ep_num in range(1, total_eps + 1)
            }
            try:
                for ft in as_completed(futures):
                    result = ft.result()
                    if result: success_eps.append(result)
            except KeyboardInterrupt:
                log("Interrupted by user. Exiting episode loop.")
                break
                
        # 4. Push to DB if we got episodes
        if success_eps:
            log(f"  Processed {len(success_eps)}/{total_eps} eps.")
            push_to_backend(drama, success_eps)
        else:
            log("  No successful episodes. Skipping DB insert.")
            
    log("\n✨ Pipeline Finish. Check Admin Panel (Pending filter).")

if __name__ == "__main__":
    main()
