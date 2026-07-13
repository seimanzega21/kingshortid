import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        urls = []
        page.on("response", lambda r: urls.append(r.url) if r.request.resource_type in ["xhr", "fetch"] else None)
        
        print("Visiting provider page...")
        await page.goto("https://vidrama.asia/provider/flareflow", timeout=60000)
        await page.wait_for_timeout(3000)
        
        print("Visiting watch page directly...")
        await page.goto("https://vidrama.asia/watch/99-mutiara-kasih--2804/1?provider=flareflow", timeout=60000)
        await page.wait_for_timeout(5000)
        
        print("\nNetwork Requests on Watch Page:")
        for u in urls:
            if "api" in u or "supabase" in u or "m3u8" in u or "mp4" in u or "vidrama" in u or "flareflow" in u:
                print(u)
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
