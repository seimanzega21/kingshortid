# -*- coding: utf-8 -*-
import asyncio
import sys

sys.stdout.reconfigure(encoding='utf-8')

async def test():
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        )
        page = await ctx.new_page()
        
        async def on_response(response):
            url = response.url
            if 'watch/satu-pedang-tebas-raja-neraka--19820' in url and response.request.method == 'POST':
                print(f"\n[MATCH POST RESPONSE] URL: {url}")
                print(f"Request Method: {response.request.method}")
                print(f"Request Headers: {dict(response.request.headers)}")
                print(f"Request Body: {response.request.post_data}")
                try:
                    body = await response.text()
                    print(f"Response Body: {body[:1000]}")
                except Exception as e:
                    print(f"Could not read body: {e}")
        
        page.on('response', on_response)
        
        url = 'https://vidrama.asia/watch/satu-pedang-tebas-raja-neraka--19820/1?provider=stardusttv'
        await page.goto(url, wait_until='load', timeout=30000)
        await asyncio.sleep(5)
        await browser.close()

asyncio.run(test())
