import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        def handle_req(req):
            if 'next-action' in req.headers:
                print(">>> INTERCEPTED NEXT-ACTION:")
                print("    URL:", req.url)
                print("    Next-Action:", req.headers['next-action'])
                print("    Payload:", req.post_data)
            if 'm3u8' in req.url or 'mp4' in req.url:
                print(">>> MEDIA URL:", req.url)

        page.on("request", handle_req)

        print("Navigating to movie page...")
        await page.goto("https://vidrama.asia/movie/pahlawan-kecil-yang-misterius--865915?provider=shortmax&lang=id", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(5000)

        # Look for the watch button or episode 1 button
        # In blob 11: watchUrl: "/watch/pahlawan-kecil-yang-misterius--865915/1?provider=shortmax&lang=id"
        print("Clicking watch button or episode 1...")
        # find button or link with watch or episode
        ep1 = await page.query_selector("a[href*='/watch/'], button:has-text('Tonton'), button:has-text('Episode 1')")
        if ep1:
            print("Found element to click:", await ep1.text_content(), await ep1.get_attribute('href'))
            await ep1.click()
            print("Clicked! Waiting 15s...")
            await page.wait_for_timeout(15000)
        else:
            print("Could not find ep1 element!")

        await browser.close()

asyncio.run(run())
