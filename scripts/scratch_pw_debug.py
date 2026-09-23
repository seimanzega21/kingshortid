import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        page.on("console", lambda msg: print(f"[CONSOLE {msg.type}] {msg.text}"))
        page.on("pageerror", lambda err: print(f"[PAGE ERROR] {err}"))

        await page.goto("https://vidrama.asia/en/watch/pahlawan-kecil-yang-misterius--865915/1?provider=shortmax&lang=id", wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(8000)

        title = await page.title()
        print("Page Title:", title)

        # Print all visible text or elements
        body_text = await page.inner_text("body")
        print("Body text snippet:\n", body_text[:500])

        await page.screenshot(path="page_screenshot.png")
        print("Screenshot saved to page_screenshot.png")

        await browser.close()

asyncio.run(run())
