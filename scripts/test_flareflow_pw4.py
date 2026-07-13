import asyncio
from playwright.async_api import async_playwright
import json

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        async def on_response(response):
            if response.request.resource_type in ["xhr", "fetch"]:
                try:
                    text = await response.text()
                    if 'm3u8' in text or 'mp4' in text or 'videos' in text:
                        print(f"FOUND VIDEO DATA IN URL: {response.url}")
                        print(text[:1000])
                except:
                    pass
                    
        page.on("response", on_response)
        
        print("Visiting watch page...")
        # Since episode 1 might redirect to detail page if we are not logged in, let's just visit the detail page first
        await page.goto("https://vidrama.asia/movie/99-mutiara-kasih--2804?provider=flareflow&lang=id", timeout=60000)
        await page.wait_for_timeout(3000)
        
        # Click on episode 1
        print("Clicking episode 1...")
        await page.evaluate("""
            const eps = document.querySelectorAll('button, a');
            for(let e of eps) {
                if(e.textContent && e.textContent.trim() === '1' || e.textContent.trim() === 'Tonton Sekarang') {
                    e.click();
                    break;
                }
            }
        """)
        
        await page.wait_for_timeout(10000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
