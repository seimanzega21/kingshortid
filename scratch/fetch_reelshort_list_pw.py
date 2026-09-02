import asyncio
import re
import json
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
        
        print("Navigating to reelshort provider page...")
        await page.goto("https://vidrama.asia/provider/reelshort", wait_until="domcontentloaded", timeout=60000)
        print("Page loaded! Waiting for Cloudflare Challenge to pass...")
        await page.wait_for_timeout(10000)
        
        # Scroll to load more if needed
        for i in range(5):
            await page.mouse.wheel(0, 2000)
            await page.wait_for_timeout(2000)
            
        html = await page.content()
        matches = re.findall(r'href="/movie/([^"?]+)', html)
        
        dramas = []
        for m in matches:
            if "--" in m:
                # slug--id
                parts = m.split("--")
                slug = parts[0]
                vid_id = parts[-1]
                if vid_id not in [d['id'] for d in dramas]:
                    dramas.append({
                        "id": vid_id,
                        "slug": slug,
                        "title": slug.replace('-', ' ').title()
                    })
        
        print(f"Found {len(dramas)} unique dramas")
        
        # Output top 20
        with open("reelshort_top20.json", "w", encoding="utf-8") as f:
            json.dump(dramas[:20], f, indent=2)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
