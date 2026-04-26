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
TARGET_SLUG   = sys.argv[1] if len(sys.argv) > 1 else "dubbingsopir-taksi-mantan-dewa-balap--846959"
TARGET_PROVIDER = sys.argv[2] if len(sys.argv) > 2 else "shortmax"

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
def compress_variants(input_url: str, base_output: str, temp_dir: Path) -> tuple[Path|None, Path|None]:
    out_720 = temp_dir / f"{base_output}.mp4"
    out_540 = temp_dir / f"{base_output}_540p.mp4"
    
    cmd_720 = [
        "ffmpeg", "-y", "-i", input_url,
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
        "-maxrate", "1200k", "-bufsize", "2400k",
        "-movflags", "+faststart", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "96k", "-ac", "2",
        str(out_720)
    ]
    
    cmd_540 = [
        "ffmpeg", "-y", "-i", input_url,
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
def sync_to_supabase(title: str, slug: str, cover_r2: str, episodes: list, desc: str = "", tags: list = None, provider: str = "shortmax"):
    try:
        payload = {
            "title": title,
            "slug": slug,
            "cover_url": cover_r2,
            "provider": provider,
            "episodes": episodes,
            "description": desc,
            "tags": tags or []
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
            headless=False,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        
        # We no longer inject tokens here. We rely on the PROFILE_DIR which has the real login session.
        # Go to drama page to get title & cover. 
        await page.goto(f"https://vidrama.asia/watch/{slug}/1?provider={TARGET_PROVIDER}", wait_until="networkidle")
        
        # Wait for React to hydrate and update the DOM with the actual title (bypassing the SSR "Eksklusif" placeholder)
        log("    [+] Waiting for React hydration...")
        try:
            await page.wait_for_function("document.querySelector('h1') && !document.querySelector('h1').innerText.includes('Eksklusif')", timeout=15000)
        except: pass
        
        # Get basic details
        metadata = await page.evaluate('''() => {
            let title = document.querySelector('h1')?.innerText || document.querySelector('meta[property="og:title"]')?.content || '';
            let desc = document.querySelector('meta[property="og:description"]')?.content || document.querySelector('meta[name="description"]')?.content || '';
            let cover = document.querySelector('meta[property="og:image"]')?.content || '';
            
            // Fix title if it contains "VIDRAMA"
            if (title.includes("VIDRAMA")) title = title.split("|")[0].trim();
            
            let tags = [];
            // Try to find tags (usually in span elements near the title)
            document.querySelectorAll('span').forEach(el => {
                let text = el.innerText.trim();
                if (text && text.length < 15 && !text.includes(' ') && !tags.includes(text)) {
                    // Primitive heuristic for tags on the page
                    if(el.className.includes('bg-') || el.className.includes('rounded')) {
                        tags.push(text);
                    }
                }
            });
            return {title, desc, cover, tags};
        }''')
        
        title = metadata['title'] or "Dubbing Sopir Taksi Mantan Dewa Balap"
        desc = metadata['desc']
        cover_url = metadata['cover']
        tags = metadata['tags']
        
        log(f"    Title: {title}")
        log(f"    Description: {desc[:50]}...")
        log(f"    Cover: {cover_url}")
        
        cover_r2 = upload_cover(cover_url, slug) if cover_url else ""
        
        episodes_data = []
        episode_num = 1
        
        while True:
            log(f"    Ep {episode_num:3}:", end="")
            
            # Check R2 first!
            r2_ep_key = f"{R2_PREFIX}/{slug}/ep{episode_num:03d}.mp4"
            r2_540_key = r2_ep_key.replace(".mp4", "_540p.mp4")
            r2_vtt_key = r2_ep_key.replace(".mp4", ".vtt")
            
            try:
                get_s3().head_object(Bucket=R2_BUCKET, Key=r2_ep_key)
                get_s3().head_object(Bucket=R2_BUCKET, Key=r2_540_key)
                log(f" already in R2")
                
                # Check if we also have subtitles in R2
                sub_urls = []
                try:
                    get_s3().head_object(Bucket=R2_BUCKET, Key=r2_vtt_key)
                    sub_urls.append({"lang": "id", "url": f"{R2_PUBLIC}/{r2_vtt_key}"})
                except: pass
                
                episodes_data.append({"number": episode_num, "videoUrl": f"{R2_PUBLIC}/{r2_ep_key}", "videoUrl540p": f"{R2_PUBLIC}/{r2_540_key}", "duration": 0, "subtitles": sub_urls})
                episode_num += 1
                continue
            except: pass

            found_m3u8 = None
            found_vtts = []
            
            def handle_response(response):
                nonlocal found_m3u8, found_vtts
                req = response.request
                if 'm3u8' in req.url:
                    if 'proxy' in req.url:
                        import urllib.parse
                        parsed = urllib.parse.urlparse(req.url)
                        qs = urllib.parse.parse_qs(parsed.query)
                        if 'url' in qs:
                            found_m3u8 = qs['url'][0]
                    else:
                        found_m3u8 = req.url
                elif '.vtt' in req.url or '.srt' in req.url:
                    if req.url not in found_vtts:
                        found_vtts.append(req.url)

            page.on("response", handle_response)
            
            try:
                await page.goto(f"https://vidrama.asia/watch/{slug}/{episode_num}?provider={TARGET_PROVIDER}", wait_until="networkidle", timeout=15000)
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
            
            # Compress directly from M3U8 URL using FFmpeg
            c720, c540 = compress_variants(found_m3u8, f"opt_ep{episode_num:03d}", drama_temp)
            if c720:
                upload_mp4(c720, r2_ep_key)
                if c540: upload_mp4(c540, r2_540_key)
                
                # Upload Subtitles if any
                sub_r2_urls = []
                if found_vtts:
                    log(" +SUBS", end="")
                    for idx, vtt_url in enumerate(found_vtts):
                        try:
                            vtt_resp = requests.get(vtt_url, timeout=15)
                            if vtt_resp.status_code == 200:
                                vtt_key = r2_ep_key.replace(".mp4", f"_{idx}.vtt") if idx > 0 else r2_vtt_key
                                get_s3().put_object(Bucket=R2_BUCKET, Key=vtt_key, Body=vtt_resp.content, ContentType="text/vtt")
                                sub_r2_urls.append({"lang": "id", "url": f"{R2_PUBLIC}/{vtt_key}"})
                        except: pass
                
                log(" OK")
                episodes_data.append({"number": episode_num, "videoUrl": f"{R2_PUBLIC}/{r2_ep_key}", "videoUrl540p": f"{R2_PUBLIC}/{r2_540_key}", "duration": 0, "subtitles": sub_r2_urls})
            else:
                log(" FAIL COMPRESS")
                break
                
            # Clean temp
            try: c720.unlink(missing_ok=True)
            except: pass
            try: c540.unlink(missing_ok=True)
            except: pass
            
            episode_num += 1

        if episodes_data:
            sync_to_supabase(title, slug, cover_r2, episodes_data, desc, tags, provider=TARGET_PROVIDER)
        
        await context.close()

if __name__ == "__main__":
    asyncio.run(scrape_drama(TARGET_SLUG))
