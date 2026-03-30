#!/usr/bin/env python3
"""
Quick probe: capture ALL API responses from iDrama watch page
to find the correct video URL endpoint pattern.
"""
import json, asyncio, sys, re
from pathlib import Path

AUTH_FILE = Path(__file__).parent / "idrama_auth.json"
AUTH_DATA = json.loads(AUTH_FILE.read_text(encoding="utf-8"))
SUPABASE_TOKEN = AUTH_DATA.get("access_token", "")
SUB_CACHE = AUTH_DATA.get("subscription_cache", {})
BROWSER_COOKIES = AUTH_DATA.get("cookies", "")

DRAMA_SLUG = "antara-dewa-atau-iblis"
DRAMA_ID   = "1600006416107"
PROVIDER   = "idrama"

from playwright.async_api import async_playwright

async def main():
    print("=== iDrama API Probe ===")
    print(f"Watch URL: https://vidrama.asia/watch/{DRAMA_SLUG}--{DRAMA_ID}/1?provider={PROVIDER}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # headful to see what happens
        ctx = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        )

        # Inject cookies
        if BROWSER_COOKIES:
            cookie_list = []
            for pair in BROWSER_COOKIES.split(";"):
                pair = pair.strip()
                if "=" in pair:
                    name, _, val = pair.partition("=")
                    cookie_list.append({
                        "name": name.strip(), "value": val.strip(),
                        "domain": "vidrama.asia", "path": "/",
                    })
            try:
                await ctx.add_cookies(cookie_list)
            except Exception as e:
                print(f"[WARN] Cookie error: {e}")

        page = await ctx.new_page()

        # Inject auth
        await page.goto("https://vidrama.asia/404", timeout=30000)
        if SUPABASE_TOKEN:
            await page.evaluate(f"""
                localStorage.setItem('sb-gkcnbnlfqdlotnjaizxx-auth-token', JSON.stringify({json.dumps(AUTH_DATA)}));
                localStorage.setItem('vidrama_subscription_cache', JSON.stringify({json.dumps(SUB_CACHE)}));
            """)
        print("[AUTH] Injected ✅")

        # Capture ALL requests
        captured = []

        async def on_request(req):
            url = req.url
            if any(k in url for k in ["api", "watch", "video", "stream", "mp4", "m3u8", "cdn", "media"]):
                print(f"  REQUEST: {req.method} {url[:120]}")

        async def on_response(resp):
            url = resp.url
            # Skip static assets
            if any(ext in url for ext in [".js", ".css", ".png", ".jpg", ".svg", ".woff", ".ico", "analytics", "gtag", "facebook"]):
                return
            print(f"  RESP {resp.status}: {url[:120]}")
            if resp.status == 200:
                ctype = resp.headers.get("content-type", "")
                if "json" in ctype:
                    try:
                        data = await resp.json()
                        print(f"    JSON keys: {list(data.keys()) if isinstance(data, dict) else type(data)}")
                        if isinstance(data, dict):
                            # Search for video URL
                            txt = json.dumps(data)
                            if any(k in txt for k in ["videoUrl", "mp4", "m3u8", "video_url", "stream"]):
                                print(f"    *** VIDEO URL FOUND ***")
                                print(f"    {txt[:500]}")
                                captured.append({"url": url, "data": data})
                    except:
                        pass
                elif "mp4" in url or "m3u8" in url:
                    print(f"    *** DIRECT MEDIA URL ***")
                    captured.append({"url": url, "data": None})

        page.on("request", on_request)
        page.on("response", on_response)

        watch_url = f"https://vidrama.asia/watch/{DRAMA_SLUG}--{DRAMA_ID}/1?provider={PROVIDER}"
        print(f"\n[NAV] Going to: {watch_url}")
        await page.goto(watch_url, timeout=45000)
        
        print("\n[WAIT] Waiting 15s for all requests to complete...")
        await page.wait_for_timeout(15000)

        # Also check video element
        print("\n[DOM] Checking video element...")
        vid_info = await page.evaluate("""
            () => {
                const v = document.querySelector('video');
                if (!v) return {found: false};
                return {
                    found: true,
                    src: v.src,
                    currentSrc: v.currentSrc,
                    tracks: Array.from(v.textTracks || []).map(t => ({kind: t.kind, src: t.id})),
                };
            }
        """)
        print(f"  Video element: {vid_info}")

        # Check all script content for URLs
        print("\n[SCAN] Scanning page content for media URLs...")
        content = await page.content()
        mp4_urls = re.findall(r'https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*', content)
        m3u8_urls = re.findall(r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*', content)
        if mp4_urls:
            print(f"  MP4s found in HTML: {mp4_urls[:3]}")
        if m3u8_urls:
            print(f"  M3U8s found in HTML: {m3u8_urls[:3]}")

        print(f"\n=== SUMMARY ===")
        print(f"Captured {len(captured)} relevant API responses")
        for c in captured:
            print(f"  {c['url'][:100]}")

        # Save all findings
        out_file = Path(__file__).parent / "idrama_probe_result.json"
        out_file.write_text(json.dumps({"captured": captured, "vid_info": vid_info}, indent=2, default=str), encoding="utf-8")
        print(f"\n  Saved to: {out_file}")
        
        print("\n[WAIT] Keeping browser open 30s for manual inspection...")
        await page.wait_for_timeout(30000)
        await browser.close()

asyncio.run(main())
