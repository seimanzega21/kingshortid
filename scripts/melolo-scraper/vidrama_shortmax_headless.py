import asyncio
import requests, json, time, os, re, sys, subprocess, shutil, boto3
from pathlib import Path
from dotenv import load_dotenv
from playwright.async_api import async_playwright

load_dotenv()
sys.stdout.reconfigure(encoding="utf-8")

# ──────────────────── CONFIG ────────────────────
BACKEND_URL   = "https://api.shortlovers.id/api"
R2_PUBLIC     = "https://stream.shortlovers.id"
R2_BUCKET     = os.getenv("R2_BUCKET_NAME") or "shortlovers"
R2_PREFIX     = "dramas/shortmax"
TEMP_DIR      = Path("C:/tmp/shortmax_mp4") if os.name == 'nt' else Path("/tmp/shortmax_mp4")
LOG_FILE      = Path(__file__).parent / "shortmax_headless.log"
PROFILE_DIR   = Path(__file__).parent / "vidrama_profile"
TARGET_SLUG   = "dubbingsopir-taksi-mantan-dewa-balap--846959"

TEMP_DIR.mkdir(parents=True, exist_ok=True)

def log(msg="", end="\n"):
    print(msg, end=end, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + end)

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

# ──────────────────── VIDEO PROCESSING ────────────────────
def download_mp4(url: str, dest: Path) -> bool:
    for attempt in range(3):
        try:
            resp = requests.get(url, timeout=120, stream=True)
            resp.raise_for_status()
            total = 0
            with open(dest, "wb") as f:
                for chunk in resp.iter_content(chunk_size=2 * 1024 * 1024):
                    f.write(chunk); total += len(chunk)
            if total > 5000: return True
        except Exception as e:
            if attempt < 2: time.sleep(1)
            else: log(f" DLerr:{str(e)[:30]}", end="")
    return False

def compress_variants(input_mp4: Path, base_output: str, temp_dir: Path) -> tuple[Path|None, Path|None]:
    out_720 = temp_dir / f"{base_output}.mp4"
    out_540 = temp_dir / f"{base_output}_540p.mp4"
    
    cmd_720 = [
        "ffmpeg", "-y", "-i", str(input_mp4),
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
        "-maxrate", "1200k", "-bufsize", "2400k",
        "-movflags", "+faststart", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "96k", "-ac", "2",
        str(out_720)
    ]
    
    cmd_540 = [
        "ffmpeg", "-y", "-i", str(input_mp4),
        "-vf", "scale=-2:540",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
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
    get_s3().upload_file(str(mp4_file), R2_BUCKET, r2_key, ExtraArgs={"ContentType": "video/mp4"})
    return f"{R2_PUBLIC}/{r2_key}"

def upload_cover(cover_url: str, slug: str) -> str | None:
    if not cover_url: return None
    try:
        resp = requests.get(cover_url, timeout=15)
        resp.raise_for_status()
        ctype = resp.headers.get("content-type", "image/jpeg")
        ext = "webp" if "webp" in ctype else "png" if "png" in ctype else "jpg"
        get_s3().put_object(Bucket=R2_BUCKET, Key=f"{R2_PREFIX}/{slug}/cover.{ext}", Body=resp.content, ContentType=ctype)
        return f"{R2_PUBLIC}/{R2_PREFIX}/{slug}/cover.{ext}"
    except: return None

# ──────────────────── SUPABASE SYNC ────────────────────
def sync_to_supabase(title: str, slug: str, cover_r2: str, episodes: list):
    try:
        payload = {
            "title": title,
            "slug": slug,
            "cover_url": cover_r2,
            "provider": "shortmax",
            "episodes": episodes
        }
        r = requests.post(f"{BACKEND_URL}/dramas", json=payload, headers={"x-admin-key": os.getenv("ADMIN_API_KEY", "")})
        if r.status_code in [200, 201]:
            log(f"    [Supabase] Synced '{title}' with {len(episodes)} episodes.")
        else:
            log(f"    [Supabase] Error {r.status_code}: {r.text}")
    except Exception as e:
        log(f"    [Supabase] Exception: {e}")

# ──────────────────── HEADLESS SCRAPER ────────────────────
async def scrape_drama(slug: str):
    log(f"\n[+] Starting scrape for: {slug}")
    drama_temp = TEMP_DIR / slug
    drama_temp.mkdir(exist_ok=True)
    
    # Check if profile exists, if not, we must run non-headless once to login
    is_first_run = not PROFILE_DIR.exists()
    headless_mode = not is_first_run

    if is_first_run:
        log("    [!] First run detected! Browser will open visibly. Please login to Vidrama and wait...")
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            headless=headless_mode,
            user_agent='Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36'
        )
        
        page = await context.new_page()
        
        if is_first_run:
            await page.goto("https://vidrama.asia/login")
            log("    [?] Please log in now. Waiting 60 seconds...")
            await asyncio.sleep(60)
            log("    [+] Saving login state... Future runs will be headless!")
        
        # Go to drama page to get title & cover
        await page.goto(f"https://vidrama.asia/watch/{slug}/1?provider=shortmax")
        
        # Get basic details
        title = "Dubbing Sopir Taksi Mantan Dewa Balap"
        try:
            title = await page.locator("h1").inner_text(timeout=5000)
        except: pass
        
        log(f"    Title: {title}")
        
        # Extract cover if possible
        cover_url = ""
        try:
            # Shortmax provider specific cover logic could be here, or use default
            pass
        except: pass
        
        cover_r2 = upload_cover(cover_url, slug) if cover_url else ""
        
        episodes_data = []
        episode_num = 1
        
        while True:
            log(f"    Ep {episode_num:3}:", end="")
            
            # Check R2 first!
            r2_ep_key = f"{R2_PREFIX}/{slug}/ep{episode_num:03d}.mp4"
            r2_540_key = r2_ep_key.replace(".mp4", "_540p.mp4")
            
            try:
                get_s3().head_object(Bucket=R2_BUCKET, Key=r2_ep_key)
                get_s3().head_object(Bucket=R2_BUCKET, Key=r2_540_key)
                log(f" already in R2")
                episodes_data.append({"number": episode_num, "videoUrl": f"{R2_PUBLIC}/{r2_ep_key}", "videoUrl540p": f"{R2_PUBLIC}/{r2_540_key}", "duration": 0})
                episode_num += 1
                continue
            except: pass

            found_m3u8 = None
            def handle_response(response):
                nonlocal found_m3u8
                req = response.request
                if 'm3u8' in req.url and 'proxy' not in req.url:
                    found_m3u8 = req.url

            page.on("response", handle_response)
            
            try:
                await page.goto(f"https://vidrama.asia/watch/{slug}/{episode_num}?provider=shortmax", wait_until="networkidle", timeout=15000)
            except Exception:
                pass
                
            # Wait a few seconds for m3u8 to be intercepted
            for _ in range(5):
                if found_m3u8: break
                await asyncio.sleep(1)
                
            page.remove_listener("response", handle_response)
            
            if not found_m3u8:
                log(" Not found (End of Drama or VIP block)")
                break
                
            log(f" Intercepted URL", end="")
            
            # Download
            raw = drama_temp / f"raw_ep{episode_num:03d}.mp4"
            if not download_mp4(found_m3u8, raw):
                log(" FAIL DL")
                break
            
            # Compress
            c720, c540 = compress_variants(raw, f"opt_ep{episode_num:03d}", drama_temp)
            if c720:
                upload_mp4(c720, r2_ep_key)
                if c540: upload_mp4(c540, r2_540_key)
                log(" OK")
                episodes_data.append({"number": episode_num, "videoUrl": f"{R2_PUBLIC}/{r2_ep_key}", "videoUrl540p": f"{R2_PUBLIC}/{r2_540_key}", "duration": 0})
            else:
                log(" FAIL COMPRESS")
                break
                
            # Clean temp
            try: raw.unlink(missing_ok=True)
            except: pass
            try: c720.unlink(missing_ok=True)
            except: pass
            try: c540.unlink(missing_ok=True)
            except: pass
            
            episode_num += 1

        if episodes_data:
            sync_to_supabase(title, slug, cover_r2, episodes_data)
        
        await context.close()

if __name__ == "__main__":
    asyncio.run(scrape_drama(TARGET_SLUG))
