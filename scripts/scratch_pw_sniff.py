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
                print("FOUND NEXT-ACTION in request:")
                print("  URL:", req.url)
                print("  Next-Action:", hdr['next-action'])
                print("  Post Data:", req.post_data)
                action_headers.append((hdr['next-action'], req.post_data))
            if 'm3u8' in req.url or 'mp4' in req.url or 'stream' in req.url:
                print("MEDIA REQUEST:", req.url[:120])

        page.on("request", handle_request)
        page.on("response", lambda res: print("RESPONSE:", res.url[:80], res.status) if ('shortmax' in res.url or 'm3u8' in res.url or 'api' in res.url) else None)

        print("Navigating to watch page...")
        try:
            await page.goto("https://vidrama.asia/watch/pahlawan-kecil-yang-misterius--865915/1?provider=shortmax&lang=id", wait_until="networkidle", timeout=30000)
        except Exception as e:
            print("Navigation finished/timed out:", e)

        await page.wait_for_timeout(5000)
        await browser.close()

asyncio.run(run())
