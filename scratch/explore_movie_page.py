# -*- coding: utf-8 -*-
import asyncio
import json
from playwright.async_api import async_playwright

async def run():
    print("Launching Playwright...")
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir='d:/kingshortid/scripts/melolo-scraper/vidrama_profile',
            headless=True
        )
        page = await context.new_page()
        
        # Intercept and print network requests
        api_requests = []
        
        async def handle_request(request):
            url = request.url
            if '/api/' in url:
                print(f"Request: {url}")
                api_requests.append(url)
                
        async def handle_response(response):
            url = response.url
            if '/api/' in url:
                try:
                    text = await response.text()
                    print(f"Response: {url} | Status: {response.status} | Body Length: {len(text)}")
                    # Save a snippet of the response body
                    print(f"Body snippet: {text[:200]}")
                except Exception as e:
                    print(f"Response error for {url}: {e}")
        
        page.on("request", handle_request)
        page.on("response", handle_response)
        
        target_url = "https://vidrama.asia/movie/penyembuhnya-istrinya--ahTFgKtAU6?provider=dramawave&lang=id-ID"
        print(f"Navigating to: {target_url}")
        
        await page.goto(target_url)
        print("Waiting 8 seconds for page loading and APIs to trigger...")
        await asyncio.sleep(8)
        
        # Save page inner_text to check for any visible titles
        title = await page.title()
        print("Page Title:", title)
        
        content = await page.inner_text("body")
        print("Page Body Text Sample:", content[:500])
        
        await context.close()

if __name__ == "__main__":
    asyncio.run(run())
