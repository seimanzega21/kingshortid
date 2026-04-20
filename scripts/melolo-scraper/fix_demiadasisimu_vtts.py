import asyncio, sys, requests
from pathlib import Path
from playwright.async_api import async_playwright

sys.path.append(str(Path(__file__).parent))
import netshort_pipeline

async def fetch_and_upload_vtts():
    drama_id = "2043863926390652929"
    slug = "demi-ada-di-sisimu"
    total_eps = 80
    
    print(f"Rescraping VTTs for {slug}...")
    
    TEMP_DIR = Path("C:/tmp/netshort_mp4")
    drama_temp = TEMP_DIR / slug
    drama_temp.mkdir(parents=True, exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={'width': 1280, 'height': 800}, user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36')
        page = await ctx.new_page()
        
        # Inject auth to bypass login
        await page.goto("https://vidrama.asia/404", timeout=30000)
        
        for ep_num in range(26, total_eps + 1):
            print(f"Checking Ep {ep_num}...", flush=True)
            watch_url = f"https://vidrama.asia/watch/{slug}--{drama_id}/{ep_num}?provider=netshort&lang=in"
            
            sub_url = None
            
            async def on_response(response):
                nonlocal sub_url
                if '/api/netshort/api/watch/' in response.url:
                    try:
                        data = await response.json()
                        subs = data.get('data', {}).get('subtitles', [])
                        if subs and isinstance(subs, list):
                            sub_url = subs[0].get('url')
                    except Exception as e:
                        print("JSON Error", e)
                        
            page.on('response', on_response)
            
            try:
                await page.goto(watch_url, timeout=30000)
                # Wait for sub_url to show up
                for _ in range(10):
                    if sub_url: break
                    await page.wait_for_timeout(1000)
            except Exception as e:
                pass
                
            page.remove_listener('response', on_response)
            
            if sub_url:
                vtt_path = drama_temp / f"ep{ep_num:03d}.vtt"
                r2_key_vtt = f"{netshort_pipeline.R2_PREFIX}/{slug}/ep{ep_num:03d}.vtt"
                
                print(f"  Got sub URL. Downloading...")
                try:
                    resp = requests.get(sub_url, timeout=30, verify=False)
                    if resp.status_code == 200:
                        with open(vtt_path, 'wb') as f:
                            f.write(resp.content)
                        
                        kb = vtt_path.stat().st_size / 1024
                        print(f"  Downloaded {kb:.1f}KB. Uploading to R2...")
                        r2_url = netshort_pipeline.upload_vtt(vtt_path, r2_key_vtt)
                        if r2_url:
                            print(f"  Success: {r2_url}")
                        vtt_path.unlink()
                    else:
                        print(f"  Download failed HTTP {resp.status_code}")
                except Exception as e:
                    print(f"  Request failed: {e}")
            else:
                print("  No sub URL found via API.")
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(fetch_and_upload_vtts())
