import asyncio
from playwright.async_api import async_playwright

async def main():
    urls = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        page.on("response", lambda r: urls.append(r.url) if r.request.resource_type in ["xhr", "fetch"] else None)
        
        print("Visiting watch page...")
        await page.goto("https://vidrama.asia/watch/99-mutiara-kasih--2804/1?provider=flareflow", timeout=60000)
        await page.wait_for_timeout(5000)
        
        print("Network XHR/Fetch Requests:")
        for u in urls:
            if "vidrama.asia/api" in u or "supabase" in u or ".m3u8" in u or ".mp4" in u or "flareflow" in u:
                print(u)
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
