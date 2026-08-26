import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        try:
            await page.goto("https://vidrama.asia/provider/stardusttv", wait_until="networkidle")
            links = await page.evaluate("Array.from(document.querySelectorAll('a[href*=\"/movie/\"]')).map(a => a.href)")
            print("LINKS:", links)
        except Exception as e:
            print("Error:", e)
        finally:
            await browser.close()

asyncio.run(main())
