import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        action_headers = []

        def handle_request(req):
            hdr = req.headers
            if 'next-action' in hdr:
                print("FOUND NEXT-ACTION:")
                print("  URL:", req.url)
                print("  Next-Action:", hdr['next-action'])
                print("  Post Data:", req.post_data)
                action_headers.append((hdr['next-action'], req.post_data))
            if 'm3u8' in req.url or 'mp4' in req.url or 'volcengine' in req.url:
                print("MEDIA URL:", req.url)

        def handle_response(res):
            if res.status != 200 and 'chunk' not in res.url:
                pass
            if 'next-action' in res.request.headers:
                print("ACTION RESPONSE STATUS:", res.status)

        page.on("request", handle_request)
        page.on("response", handle_response)

        print("Navigating to watch page with domcontentloaded...")
        try:
            await page.goto("https://vidrama.asia/en/watch/pahlawan-kecil-yang-misterius--865915/1?provider=shortmax&lang=id", wait_until="domcontentloaded", timeout=60000)
            print("Loaded DOM, waiting 10s for scripts...")
            await page.wait_for_timeout(10000)
        except Exception as e:
            print("Error:", e)

        # Check video src if any
        try:
            video_src = await page.evaluate("() => document.querySelector('video')?.src || document.querySelector('source')?.src")
            print("Video element src:", video_src)
        except:
            pass

        await browser.close()

asyncio.run(run())
