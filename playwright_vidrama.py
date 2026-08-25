import asyncio
from playwright.async_api import async_playwright
import json

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        requests_seen = []
        
        page.on("request", lambda request: requests_seen.append(request.url))
        
        print("Navigating...")
        await page.goto("https://vidrama.asia/movie/balas-budi-ular-suci--2059089132047048706?provider=netshortv2&lang=id", wait_until="networkidle")
        
        print("Finding all API calls...")
        for url in requests_seen:
            if "google" not in url and "facebook" not in url:
                print(url)
                
        await browser.close()

asyncio.run(run())
