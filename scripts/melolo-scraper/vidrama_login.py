import asyncio
from playwright.async_api import async_playwright
import sys
from pathlib import Path

PROFILE_DIR = Path("d:/kingshortid/scripts/melolo-scraper/vidrama_profile")

async def do_login():
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            headless=False,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            viewport={'width': 1280, 'height': 720}
        )
        
        page = await browser.new_page()
        await page.goto("https://vidrama.asia")
        print("[+] Browser terbuka! Silakan login secara manual.")
        
        # Wait until user closes the browser manually
        try:
            while len(browser.pages) > 0:
                await asyncio.sleep(1)
        except:
            pass
        
        print("[+] Browser ditutup. Session tersimpan!")

if __name__ == "__main__":
    asyncio.run(do_login())
