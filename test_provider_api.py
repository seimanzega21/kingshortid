# -*- coding: utf-8 -*-
import asyncio
import sys

sys.stdout.reconfigure(encoding='utf-8')

async def test():
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            locale='id-ID'
        )
        
        await ctx.add_cookies([
            {'name': 'global_ui_lang', 'value': 'id', 'domain': 'vidrama.asia', 'path': '/'},
            {'name': 'next-locale', 'value': 'id', 'domain': 'vidrama.asia', 'path': '/'},
            {'name': 'NEXT_LOCALE', 'value': 'id', 'domain': 'vidrama.asia', 'path': '/'},
        ])
        
        page = await ctx.new_page()
        
        async def on_response(response):
            url = response.url
            if any(ext in url.lower() for ext in ['.js', '.css', '.png', '.jpg', '.jpeg', '.webp', '.svg', '.woff', '.ttf', 'google-analytics', 'tiktok', 'histats']):
                return
            print(f"RESPONSE [{response.status}]: {url}")
            try:
                if 'json' in response.headers.get('content-type', ''):
                    print(f"  JSON: {str(await response.json())[:300]}")
            except:
                pass
                
        page.on('response', on_response)
        
        url = 'https://vidrama.asia/id/provider/stardusttv'
        print(f"Loading: {url}")
        await page.goto(url, wait_until='load', timeout=30000)
        await asyncio.sleep(5)
        await browser.close()

asyncio.run(test())
