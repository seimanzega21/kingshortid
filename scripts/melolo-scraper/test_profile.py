import asyncio
import sys
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(user_data_dir='d:/kingshortid/scripts/melolo-scraper/vidrama_profile', headless=True)
        page = await browser.new_page()
        await page.goto('https://vidrama.asia/movie/cahaya-di-balik-gelap--1987705627844739073?provider=shortmax', wait_until='networkidle')
        content = await page.content()
        with open('d:/kingshortid/scripts/melolo-scraper/test_profile.html', 'w', encoding='utf-8') as f:
            f.write(content)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
