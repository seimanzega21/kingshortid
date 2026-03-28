#!/usr/bin/env python3
"""
NETSHORT PROBE SCRIPT
======================
Login dengan akun VIP, buka /provider/netshort,
intercept semua network request, temukan:
1. API endpoint untuk list drama
2. Cara fetch episode list
3. Video URL format (MP4)
"""
import asyncio, json, re
from pathlib import Path
from playwright.async_api import async_playwright

EMAIL    = "seimanzega21@gmail.com"
PASSWORD = "Radhika05"

async def main():
    print("=" * 60)
    print("  NETSHORT API PROBE")
    print("=" * 60)

    captured_requests = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # non-headless to debug
        ctx = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
        )

        # --- Intercept all requests ---
        async def capture(route):
            req = route.request
            url = req.url
            method = req.method
            hdrs = dict(req.headers)
            body = ""
            if method == "POST":
                try: body = req.post_data or ""
                except: pass
            captured_requests.append({
                "url": url, "method": method,
                "headers": hdrs, "body": body[:500]
            })
            await route.continue_()

        page = await ctx.new_page()
        await page.route("**/*", capture)

        # Capture responses too
        video_urls = []
        async def on_response(response):
            url = response.url
            if any(x in url.lower() for x in [".mp4", ".m3u8", "/video/", "playback", "/stream"]):
                video_urls.append(url)
                print(f"\n  🎬 VIDEO URL: {url[:120]}")

        page.on("response", on_response)

        # ─── Step 1: Login ───
        print("\n[1] Logging in to Vidrama...")
        await page.goto("https://vidrama.asia/login", timeout=30000)
        await page.wait_for_timeout(3000)

        # Fill email
        await page.fill("input[type='email'], input[name='email'], input[placeholder*='email' i]", EMAIL)
        await page.wait_for_timeout(500)

        # Fill password
        await page.fill("input[type='password']", PASSWORD)
        await page.wait_for_timeout(500)

        # Submit
        await page.click("button[type='submit'], button:has-text('Masuk'), button:has-text('Login')")
        await page.wait_for_timeout(5000)
        print(f"  Current URL: {page.url}")

        # ─── Step 2: Go to Netshort provider page ───
        print("\n[2] Opening /provider/netshort...")
        captured_requests.clear()
        await page.goto("https://vidrama.asia/provider/netshort", timeout=30000)
        await page.wait_for_timeout(5000)

        # Scroll to load more
        for i in range(5):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)
            links = await page.query_selector_all("a[href*='/movie/']")
            print(f"  Scroll {i+1}: {len(links)} drama links found")

        # Get drama links
        links = await page.query_selector_all("a[href*='/movie/']")
        dramas = []
        for link in links:
            href = await link.get_attribute("href") or ""
            if "/movie/" not in href:
                continue
            # Extract title and id from href
            # Pattern: /movie/{slug}--{id}?provider=netshort
            match = re.search(r"/movie/(.+?)--(\d+)", href)
            if not match:
                continue
            slug = match.group(1)
            drama_id = match.group(2)
            title = ""
            try:
                img = await link.query_selector("img")
                if img:
                    title = (await img.get_attribute("alt")) or ""
            except: pass
            if not title:
                title = slug.replace("-", " ").title()
            cover = ""
            try:
                img = await link.query_selector("img")
                if img:
                    cover = (await img.get_attribute("src")) or ""
            except: pass
            entry = {"slug": slug, "id": drama_id, "title": title, "cover": cover}
            if entry not in dramas:
                dramas.append(entry)

        print(f"\n  Found {len(dramas)} unique dramas")

        # Print API requests captured
        api_calls = [r for r in captured_requests if "api" in r["url"].lower() or r["method"] == "POST"]
        print(f"\n  API calls captured: {len(api_calls)}")
        for r in api_calls[:10]:
            print(f"  [{r['method']}] {r['url'][:100]}")
            if r.get("headers", {}).get("next-action"):
                print(f"    next-action: {r['headers']['next-action']}")
            if r.get("body"):
                print(f"    body: {r['body'][:100]}")

        # ─── Step 3: Open first drama + first episode ───
        if dramas:
            drama = dramas[0]
            movie_url = f"https://vidrama.asia/movie/{drama['slug']}--{drama['id']}?provider=netshort"
            print(f"\n[3] Opening drama: {drama['title']}")
            print(f"  URL: {movie_url}")

            captured_requests.clear()
            await page.goto(movie_url, timeout=30000)
            await page.wait_for_timeout(5000)

            # Get description, genres
            desc_el = await page.query_selector('[class*="synopsis"], [class*="description"], [class*="desc"]')
            description = (await desc_el.inner_text()).strip()[:500] if desc_el else ""
            print(f"  Description: {description[:100]}")

            genre_els = await page.query_selector_all('[class*="genre"], [class*="tag"], [class*="category"]')
            genres = []
            for g in genre_els[:10]:
                t = (await g.inner_text()).strip()
                if t and len(t) < 30:
                    genres.append(t)
            print(f"  Genres: {genres}")

            # Get episode links
            ep_links = await page.query_selector_all("a[href*='/watch/'], a[href*='/episode/'], [class*='episode'] a")
            print(f"  Episode links: {len(ep_links)}")

            # API calls on drama page
            drama_api = [r for r in captured_requests if r["method"] == "POST" or "api" in r["url"].lower()]
            print(f"\n  Drama page API calls:")
            for r in drama_api[:10]:
                print(f"  [{r['method']}] {r['url'][:100]}")
                if r.get("headers", {}).get("next-action"):
                    print(f"    next-action: {r['headers']['next-action']}")
                if r.get("body"):
                    print(f"    body: {r['body'][:200]}")

            # ─── Step 4: Open episode 1 ───
            if ep_links:
                ep_url = await ep_links[0].get_attribute("href") or ""
                if ep_url and not ep_url.startswith("http"):
                    ep_url = "https://vidrama.asia" + ep_url
                print(f"\n[4] Opening Episode 1: {ep_url}")

                captured_requests.clear()
                await page.goto(ep_url, timeout=30000)
                await page.wait_for_timeout(7000)

                # Get video element
                video_src = await page.evaluate("""() => {
                    const v = document.querySelector('video');
                    if (!v) return null;
                    return { src: v.src, currentSrc: v.currentSrc };
                }""")
                print(f"  Video element: {video_src}")

                # Print all API/POST calls
                ep_api = [r for r in captured_requests if r["method"] == "POST" or ".mp4" in r["url"] or ".m3u8" in r["url"]]
                print(f"\n  Episode page API calls:")
                for r in ep_api[:15]:
                    print(f"  [{r['method']}] {r['url'][:120]}")
                    if r.get("headers", {}).get("next-action"):
                        print(f"    next-action: {r['headers']['next-action']}")
                    if r.get("body"):
                        print(f"    body: {r['body'][:300]}")

        # Save results
        result = {
            "dramas_sample": dramas[:5],
            "total_dramas_found": len(dramas),
            "video_urls_captured": video_urls,
            "all_captured": [r for r in captured_requests if r["method"] == "POST"],
        }
        out = Path("netshort_probe_result.json")
        out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\n\nSaved: {out.absolute()}")

        print(f"\n{'='*60}")
        print(f"  Total dramas: {len(dramas)}")
        print(f"  Video URLs: {len(video_urls)}")
        print(f"{'='*60}")

        await page.wait_for_timeout(3000)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
