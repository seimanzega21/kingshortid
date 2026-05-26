import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto('https://vidrama.asia/movie/jangan-tangisi-kepergianku--42000000999?provider=dramabox3&lang=in')
        title = await page.title()
        desc = await page.locator('meta[name="description"]').get_attribute('content')
        img = await page.locator('meta[property="og:image"]').get_attribute('content')
        print(f"TITLE: {title}")
        print(f"DESC: {desc}")
        print(f"IMG: {img}")
        await browser.close()

asyncio.run(main())
