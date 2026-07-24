import asyncio
import re
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)
        
        async def handle_request(route, request):
            if "google-analytics.com" in request.url or "clarity.ms" in request.url:
                await route.abort()
            else:
                await route.continue_()

        await page.route("**/*", handle_request)
        
        # intercept requests
        page.on("request", lambda req: print(f"REQ: {req.resource_type} - {req.url}") if req.resource_type in ["media", "fetch", "xhr"] or "m3u8" in req.url or "mp4" in req.url else None)
        
        print("Navigating to reelshort video page...")
        await page.goto("https://vidrama.asia/watch/dua-saudari-terlahir-kembali--6a4f15befff543123200001f/1?provider=reelshort", wait_until="networkidle", timeout=60000)
        print("Page loaded!")
        
        # Dump HTML
        html = await page.content()
        
        # intercept requests
        page.on("request", lambda req: print(f"REQ: {req.resource_type} - {req.url}") if req.resource_type in ["media", "fetch", "xhr"] or "m3u8" in req.url or "mp4" in req.url else None)
        
        # Take a screenshot
        await page.screenshot(path="reelshort_screenshot.png", full_page=True)
        print("Screenshot saved to reelshort_screenshot.png")
        
        with open("reelshort_page.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("HTML saved to reelshort_page.html")
        
        await page.wait_for_timeout(5000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
