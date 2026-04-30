import asyncio
from playwright.async_api import async_playwright
from pathlib import Path
import json

PROFILE_DIR = Path("d:/kingshortid/scripts/melolo-scraper/vidrama_profile")

async def extract_cookies():
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            headless=True
        )
        cookies = await browser.cookies()
        await browser.close()
        
        cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
        print(cookie_str)
        return cookie_str

if __name__ == "__main__":
    asyncio.run(extract_cookies())
