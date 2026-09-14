import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        # log all network requests
        def on_request(req):
            url = req.url
            if any(k in url for k in ['api', 'dramabox', 'video', 'm3u8', 'mp4', 'stream']):
                print(f"[{req.resource_type}] {req.method} {url}")
        page.on("request", on_request)

        print("Navigating to watch page...")
        try:
            await page.goto("https://vidrama.asia/watch/hati-yang-dihancurkan--42000025364/1?provider=dramabox&lang=in", wait_until="load", timeout=60000)
            print("Page loaded! Waiting 10 seconds for video playback...")
            await page.wait_for_timeout(10000)

            # Check video element or iframe
            video_src = await page.evaluate("() => document.querySelector('video')?.src || document.querySelector('source')?.src || 'No video tag'")
            print(f"Video element src: {video_src}")
        except Exception as e:
            print("Error navigating:", e)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
