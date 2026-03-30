#!/usr/bin/env python3
"""
Quick test: hit DotDrama API directly with auth headers
and use JS evaluate to get the video URL from the page.
"""
import json, asyncio, requests, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

AUTH_FILE = Path(__file__).parent / "idrama_auth.json"
AUTH_DATA = json.loads(AUTH_FILE.read_text(encoding="utf-8"))
TOKEN = AUTH_DATA.get("access_token", "")
DRAMA_ID = "1600006416107"

print("=" * 60)
print("TEST 1: Direct DotDrama REST API")
print("=" * 60)

# Test the DotDrama detail API
url = f"https://vidrama.asia/api/dotdrama/api/v1/dramas/{DRAMA_ID}?lang=id"
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
    "Referer": "https://vidrama.asia/",
    "Accept": "application/json",
}
print(f"GET {url}")
try:
    r = requests.get(url, headers=headers, timeout=20, verify=False)
    print(f"Status: {r.status_code}")
    print(f"Content-Type: {r.headers.get('content-type', '')}")
    if r.status_code == 200:
        try:
            data = r.json()
            keys = list(data.keys()) if isinstance(data, dict) else type(data)
            print(f"Keys: {keys}")
            txt = json.dumps(data)
            print(f"Response preview: {txt[:500]}")
        except:
            print(f"Not JSON. Raw: {r.text[:500]}")
    else:
        print(f"Response: {r.text[:300]}")
except Exception as e:
    print(f"Error: {e}")

print()
print("=" * 60)
print("TEST 2: DotDrama Episode API pattern")
print("=" * 60)

# Try common episode endpoint patterns
patterns = [
    f"https://vidrama.asia/api/dotdrama/api/v1/dramas/{DRAMA_ID}/episodes/1?lang=id",
    f"https://vidrama.asia/api/dotdrama/api/v1/episode?dramaId={DRAMA_ID}&episode=1&lang=id",
    f"https://vidrama.asia/api/dotdrama/watch?id={DRAMA_ID}&ep=1",
    f"https://vidrama.asia/api/watch?provider=idrama&id={DRAMA_ID}&episode=1",
    f"https://vidrama.asia/api/idrama/api/watch/{DRAMA_ID}/1",
]
for ep_url in patterns:
    try:
        r = requests.get(ep_url, headers=headers, timeout=10, verify=False)
        print(f"  {r.status_code} {ep_url[:80]}")
        if r.status_code == 200:
            print(f"  BODY: {r.text[:300]}")
    except Exception as e:
        print(f"  ERR {ep_url[:60]}: {str(e)[:50]}")

print()
print("=" * 60)
print("TEST 3: Playwright JS Evaluate — grab video src after load")
print("=" * 60)

from playwright.async_api import async_playwright

async def test_playwright():
    cdata = AUTH_DATA
    sub = AUTH_DATA.get("subscription_cache", {})
    browser_cookies = AUTH_DATA.get("cookies", "")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
        )
        # Inject cookies
        cookie_list = []
        for pair in browser_cookies.split(";"):
            pair = pair.strip()
            if "=" in pair:
                name, _, val = pair.partition("=")
                cookie_list.append({"name": name.strip(), "value": val.strip(), "domain": "vidrama.asia", "path": "/"})
        try:
            await ctx.add_cookies(cookie_list)
        except: pass

        page = await ctx.new_page()
        await page.goto("https://vidrama.asia/404", timeout=20000)
        await page.evaluate(f"""
            localStorage.setItem('sb-gkcnbnlfqdlotnjaizxx-auth-token', JSON.stringify({json.dumps(cdata)}));
            localStorage.setItem('vidrama_subscription_cache', JSON.stringify({json.dumps(sub)}));
        """)

        all_requests = []
        async def on_req(req):
            all_requests.append(f"{req.method} {req.url[:120]}")
        async def on_resp(resp):
            if resp.status == 200 and "json" in resp.headers.get("content-type", ""):
                try:
                    d = await resp.json()
                    if isinstance(d, dict):
                        txt = json.dumps(d)
                        if any(k in txt.lower() for k in ["videourl", "mp4", "pphys", "stream", "video_url"]):
                            print(f"  *** JSON with video: {resp.url[:100]}")
                            print(f"      {txt[:400]}")
                except: pass
            # Also log redirect/media
            if any(x in resp.url for x in [".mp4", ".m3u8", "video-proxy"]):
                print(f"  MEDIA RESP {resp.status}: {resp.url[:120]}")
                all_requests.append(f"MEDIA:{resp.url}")

        page.on("request", on_req)
        page.on("response", on_resp)

        watch_url = f"https://vidrama.asia/watch/antara-dewa-atau-iblis--1600006416107/1?provider=idrama"
        print(f"Loading: {watch_url}")
        await page.goto(watch_url, wait_until="domcontentloaded", timeout=45000)
        print("Waiting 20s for all async requests...")
        await page.wait_for_timeout(20000)

        # Try to get video src via JS
        vid_data = await page.evaluate("""
            () => {
                const v = document.querySelector('video');
                if (!v) return {found: false, src: null};
                return {
                    found: true,
                    src: v.src || v.currentSrc || null,
                    attrs: {
                        src: v.getAttribute('src'),
                        'data-src': v.getAttribute('data-src'),
                    }
                };
            }
        """)
        print(f"\nVideo element: {vid_data}")

        # JS: get all video URLs from the window/React fiber
        bundle_data = await page.evaluate("""
            () => {
                // Try to find video URL in Next.js __NEXT_DATA__
                try {
                    const nd = window.__NEXT_DATA__;
                    if (nd) return JSON.stringify(nd).substring(0, 2000);
                } catch(e) {}
                return null;
            }
        """)
        if bundle_data:
            print(f"\n__NEXT_DATA__ snippet: {bundle_data[:800]}")

        # Print all captured requests (filter interesting ones)
        print(f"\nTotal requests captured: {len(all_requests)}")
        interesting = [r for r in all_requests if any(k in r.lower() for k in ["api", "watch", "video", "dotdrama", "idrama", "media", "stream", "mp4"])]
        for r in interesting[:30]:
            print(f"  {r[:130]}")

        await browser.close()

asyncio.run(test_playwright())
