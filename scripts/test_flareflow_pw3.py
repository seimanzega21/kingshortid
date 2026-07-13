import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("Visiting watch page directly...")
        resp = await page.goto("https://vidrama.asia/watch/99-mutiara-kasih--2804/1?provider=flareflow", timeout=60000)
        await page.wait_for_timeout(5000)
        
        html = await page.content()
        with open("d:/kingshortid/scripts/test_flareflow_html.html", "w", encoding="utf-8") as f:
            f.write(html)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
