#!/usr/bin/env python3
"""
NETSHORT PLAYWRIGHT PROBE — Inject Auth Token via localStorage
=============================================================
Strategy: Inject Supabase JWT directly into browser localStorage
→ No Cloudflare login page needed!
→ Intercept all RSC POST calls to find next-action tokens
→ Extract drama list from /provider/netshort
→ Get episode video URLs from awscdn.netshort.com
"""
import asyncio, json, re
from pathlib import Path
from playwright.async_api import async_playwright

# Supabase auth data from user's browser
AUTH_DATA = {
    "access_token": "eyJhbGciOiJFUzI1NiIsImtpZCI6ImY0NTAxYzU1LTY5ZmMtNDczNy05NzFkLTU1OTVjZmRmZDAwNSIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL2drY25ibmxmcWRsb3RuamFpenh4LnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI2ZjNlNWMxNS1hMjFjLTRkMTAtYjg2Yy1lODgxNzBlN2I3MmQiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzc0NjkzMzkxLCJpYXQiOjE3NzQ2ODk3OTEsImVtYWlsIjoic2VpbWFuemVnYTIxQGdtYWlsLmNvbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZ29vZ2xlIiwicHJvdmlkZXJzIjpbImdvb2dsZSIsImVtYWlsIl19LCJ1c2VyX21ldGFkYXRhIjp7ImF2YXRhcl91cmwiOiJodHRwczovL2xoMy5nb29nbGV1c2VyY29udGVudC5jb20vYS9BQ2c4b2NLTHVLNzltN2xuOWdBcXJRVEhNVFFDZTFRR3B3Vy10dHh2RW1lNWUzSTF2OHBubGpvPXM5Ni1jIiwiZW1haWwiOiJzZWltYW56ZWdhMjFAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZ1bGxfbmFtZSI6InNlaW1hbiB6ZWdhIiwiaXNzIjoiaHR0cHM6Ly9hY2NvdW50cy5nb29nbGUuY29tIiwibmFtZSI6InNlaW1hbiB6ZWdhIiwicGhvbmVfdmVyaWZpZWQiOmZhbHNlLCJwaWN0dXJlIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EvQUNnOG9jS0x1Szc5bTdsbjlnQXFyUVRITVRRQ2UxUUdwd1ctdHR4dkVtZTVlM0kxdjhwbmxqbz1zOTYtYyIsInByb3ZpZGVyX2lkIjoiMTA3NjA4MDAzMDIzNjk0ODg5MzE3Iiwic3ViIjoiMTA3NjA4MDAzMDIzNjk0ODg5MzE3In0sInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiYWFsIjoiYWFsMSIsImFtciI6W3sibWV0aG9kIjoicGFzc3dvcmQiLCJ0aW1lc3RhbXAiOjE3NzQ2ODk3OTF9XSwic2Vzc2lvbl9pZCI6ImE0NTM5MWFjLWM4YWItNDI3ZC05OTNkLWFhZDYxMjI0MTJlYyIsImlzX2Fub255bW91cyI6ZmFsc2V9.V3BqHWPqGHVkkE9Sqb4IOJcPO51ZblyWk_oZbfyJgP1y9dh_HUV4Snd_AKkEoeWLELPlEcjpLSIu6OP7Q9K-kw",
    "token_type": "bearer",
    "expires_in": 3600,
    "expires_at": 1774693391,
    "refresh_token": "l35sdnbtaykg",
    "user": {"id": "6f3e5c15-a21c-4d10-b86c-e88170e7b72d", "email": "seimanzega21@gmail.com"},
    "weak_password": None
}

DRAMA_SAMPLES = [
    {"id": "2033755298681847810", "slug": "si-jenius-tak-sadar-diri", "title": "Si Jenius Tak Sadar Diri"},
    {"id": "2034897075744800770", "slug": "gejolak-keluarga-konglomerat", "title": "Gejolak Keluarga Konglomerat"},
]

async def main():
    print("=" * 60)
    print("  NETSHORT PLAYWRIGHT PROBE (localStorage Auth)")
    print("=" * 60)

    captured_requests = []  # All POST requests
    video_urls = []         # Netshort MP4 URLs

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        ctx = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
        )

        # ─── Intercept ALL requests ───
        async def on_request(request):
            hdrs = request.headers
            url  = request.url
            if request.method == "POST" or "next-action" in hdrs:
                entry = {
                    "url": url, "method": request.method,
                    "next_action": hdrs.get("next-action", ""),
                    "auth": hdrs.get("authorization", "")[:50] if hdrs.get("authorization") else "",
                    "body": ""
                }
                try: entry["body"] = request.post_data or ""
                except: pass
                captured_requests.append(entry)

        async def on_response(response):
            url = response.url
            if "awscdn.netshort.com" in url or ".mp4" in url.lower():
                video_urls.append(url)
                print(f"\n  🎬 VIDEO: {url[:100]}")

        page = await ctx.new_page()
        page.on("request", on_request)
        page.on("response", on_response)

        # ─── Step 1: Inject auth via localStorage ───
        print("\n[1] Injecting auth token via localStorage...")
        # Go to vidrama.asia first (empty page to set localStorage)
        await page.goto("https://vidrama.asia", timeout=30000)
        await page.wait_for_timeout(3000)

        # Inject the Supabase auth token into localStorage
        await page.evaluate(f"""
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
        print("  ✅ Auth token injected!")

        # ─── Step 2: Navigate to /provider/netshortv2 → get drama list ───
        print("\n[2] Loading /provider/netshortv2 drama list...")
        captured_requests.clear()
        await page.goto("https://vidrama.asia/provider/netshortv2", timeout=30000)
        await page.wait_for_timeout(5000)

        # Scroll to load all dramas
        dramas = []
        for scroll in range(10):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1500)
            links = await page.query_selector_all("a[href*='/movie/']")
            print(f"  Scroll {scroll+1}: {len(links)} drama links")
            if len(links) > len(dramas):
                dramas_temp = []
                for link in links:
                    href = await link.get_attribute("href") or ""
                    m = re.search(r"/movie/(.+?)--(\d{10,})", href)
                    if not m: continue
                    title = ""
                    try:
                        img = await link.query_selector("img")
                        if img: title = await img.get_attribute("alt") or ""
                    except: pass
                    cover = ""
                    try:
                        img = await link.query_selector("img")
                        if img: cover = await img.get_attribute("src") or ""
                    except: pass
                    entry = {"slug": m.group(1), "id": m.group(2), "title": title or m.group(1), "cover": cover}
                    if entry["id"] not in {d["id"] for d in dramas_temp}:
                        dramas_temp.append(entry)
                dramas = dramas_temp

        print(f"\n  📺 Total dramas: {len(dramas)}")
        for d in dramas[:5]:
            print(f"    [{d['id']}] {d['title'][:50]}, Cover: {d['cover'][:60]}")

        # Print POST requests captured during provider page load
        provider_posts = [r for r in captured_requests if r["method"] == "POST" or r["next_action"]]
        print(f"\n  POST requests on provider page: {len(provider_posts)}")
        for r in provider_posts[:5]:
            print(f"  [{r['method']}] {r['url'][:80]}")
            if r["next_action"]:
                print(f"    next-action: {r['next_action']}")

        # Save drama list
        Path("netshort_dramas_list.json").write_text(
            json.dumps(dramas, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"  Saved: netshort_dramas_list.json ({len(dramas)} dramas)")

        # ─── Step 3: Load one drama movie page ───
        if dramas:
            drama = dramas[0]
            movie_url = f"https://vidrama.asia/movie/{drama['slug']}--{drama['id']}?provider=netshortv2"
            print(f"\n[3] Loading drama: {drama['title']}")
            captured_requests.clear()
            await page.goto(movie_url, timeout=30000)
            await page.wait_for_timeout(5000)

            # Extract description, genre, episode count
            desc = ""
            try:
                for sel in ['[class*="synopsis"]', '[class*="description"]', '[class*="desc"]', 'p']:
                    el = await page.query_selector(sel)
                    if el:
                        t = (await el.inner_text()).strip()
                        if len(t) > 30:
                            desc = t[:500]; break
            except: pass

            ep_count_text = ""
            try:
                el = await page.query_selector('[class*="episode"]')
                if el: ep_count_text = (await el.inner_text()).strip()[:50]
            except: pass

            print(f"  Description: {desc[:80]}")
            print(f"  Episodes indicator: {ep_count_text}")

            # Episode buttons
            ep_btns = await page.query_selector_all("[class*='episode'] a, a[href*='/watch/']")
            print(f"  Episode links: {len(ep_btns)}")

            # Drama page POST requests
            drama_posts = [r for r in captured_requests if r["method"] == "POST" or r["next_action"]]
            print(f"\n  POST requests on drama page: {len(drama_posts)}")
            for r in drama_posts[:10]:
                print(f"  [{r['method']}] {r['url'][:100]}")
                if r["next_action"]:
                    print(f"    ★ next-action: {r['next_action']}")
                if r["body"]:
                    print(f"    body: {r['body'][:150]}")

        # ─── Step 4: Click Episode 1 → get video URL ───
        print("\n[4] Clicking Episode 1...")
        ep_links = await page.query_selector_all("a[href*='/watch/'], a[href*='/movie/'][href*='/1?']")
        if not ep_links:
            # Try clicking any element that says "1" in episode area
            ep_links = await page.query_selector_all("[class*='episode']")

        if ep_links:
            captured_requests.clear()
            await ep_links[0].click()
            await page.wait_for_timeout(8000)

            video_src = await page.evaluate("""() => {
                const v = document.querySelector('video');
                return v ? { src: v.src, currentSrc: v.currentSrc } : null;
            }""")
            print(f"  Video element: {video_src}")

            ep1_posts = [r for r in captured_requests if r["method"] == "POST" or r["next_action"] or "netshort" in r["url"]]
            print(f"\n  POST requests on episode page: {len(ep1_posts)}")
            for r in ep1_posts[:15]:
                print(f"  [{r['method']}] {r['url'][:120]}")
                if r["next_action"]:
                    print(f"    ★★ NEXT-ACTION: {r['next_action']}")
                if r["body"]:
                    print(f"    body: {r['body'][:200]}")
        else:
            print("  No episode links found - trying URL directly")
            if dramas:
                d = dramas[0]
                watch_url = f"https://vidrama.asia/watch/{d['slug']}--{d['id']}/1?provider=netshortv2"
                captured_requests.clear()
                await page.goto(watch_url, timeout=30000)
                await page.wait_for_timeout(8000)

                video_src = await page.evaluate("() => { const v = document.querySelector('video'); return v?.src || v?.currentSrc; }")
                print(f"  Video src: {video_src}")

                for r in captured_requests:
                    if r["next_action"] or "netshort" in r["url"].lower():
                        print(f"  ★ [{r['method']}] {r['url'][:120]}")
                        if r["next_action"]: print(f"    NEXT-ACTION: {r['next_action']}")
                        if r["body"]: print(f"    body: {r['body'][:200]}")

        # ─── Summary ───
        print(f"\n{'='*60}")
        print(f"  Dramas found: {len(dramas)}")
        print(f"  Video URLs captured: {len(video_urls)}")
        for v in video_urls:
            print(f"    {v[:100]}")

        # Save all results
        result = {
            "dramas": dramas[:10],
            "total_dramas": len(dramas),
            "video_urls": video_urls,
            "post_requests": [r for r in captured_requests if r["next_action"]],
        }
        Path("netshort_probe_result.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print("  Saved: netshort_probe_result.json")
        print(f"{'='*60}")

        await page.wait_for_timeout(3000)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
