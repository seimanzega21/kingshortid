import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Listen for all network requests
        page.on("request", lambda request: print(f"Request: {request.url}"))
        
        url = 'https://vidrama.asia/movie/ratu-tersembunyi-membalas--rz3UJ5zFl4?provider=dramawavev2&lang=in'
        print(f"Loading {url}...")
        try:
            await page.goto(url, wait_until="networkidle")
        except Exception as e:
            print("Error loading page:", e)
        
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
