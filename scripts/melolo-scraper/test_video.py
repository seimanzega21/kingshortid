import asyncio
import sys
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(user_data_dir='d:/kingshortid/scripts/melolo-scraper/vidrama_profile', headless=True)
        page = await browser.new_page()
        
        def handle_response(response):
            # Print all response URLs
            print(f"[NETWORK] {response.url}")
                
        page.on("response", handle_response)
        
        print("[*] Navigating to watch page...")
        await page.goto('https://vidrama.asia/watch/cahaya-di-balik-gelap--1987705627844739073/1?provider=netshort', wait_until='networkidle')
        await asyncio.sleep(5)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
