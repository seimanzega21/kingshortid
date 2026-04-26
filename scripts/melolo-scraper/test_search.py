import asyncio
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto('https://vidrama.asia/search?q=Tuan%20Gelap', wait_until='networkidle')
        html = await page.content()
        print(html[:2000])
        print("LINKS:")
        for handle in await page.query_selector_all('a'):
            href = await handle.get_attribute('href')
            print(" -", href)
        await browser.close()

asyncio.run(test())
