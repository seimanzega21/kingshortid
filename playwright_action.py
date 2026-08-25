import asyncio
from playwright.async_api import async_playwright
import json

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        async def handle_request(request):
            if request.method == "POST" and "Next-Action" in request.headers:
                print("ACTION ID FOUND:", request.headers["Next-Action"])
                
        page.on("request", handle_request)
        
        print("Navigating...")
        await page.goto("https://vidrama.asia/movie/dijulukisang-pembangkit-negara--843859?provider=shortmax&lang=id", wait_until="networkidle")
        
        await browser.close()

asyncio.run(run())
