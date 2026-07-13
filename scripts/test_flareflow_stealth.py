import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # using standard desktop user agent
        page = await browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
        await stealth(page)
        
        async def on_response(response):
            if response.request.resource_type in ["xhr", "fetch"]:
                try:
                    text = await response.text()
                    if 'videos' in text or '.mp4' in text or '.m3u8' in text:
                        print(f"FOUND VIDEO DATA IN URL: {response.url}")
                        print(text[:1500])
                except:
                    pass
                    
        page.on("response", on_response)
        
        print("Visiting detail page...")
        await page.goto("https://vidrama.asia/movie/99-mutiara-kasih--2804?provider=flareflow&lang=id", timeout=60000)
        await page.wait_for_timeout(3000)
        
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
