#!/usr/bin/env python3
"""
Quick debug: try headed Playwright + longer wait + check what's loaded.
Also try to find the API endpoint vidrama.asia uses internally.
"""
import json, asyncio, re
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # HEADED mode
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        # Capture all API calls the page makes
        api_calls = []
        async def on_response(response):
            url = response.url
            ct = response.headers.get('content-type', '')
            if 'json' in ct or 'api' in url.lower() or 'supabase' in url.lower() or 'drama' in url.lower():
                try:
                    body = await response.text()
                    api_calls.append({
                        'url': url,
                        'status': response.status,
                        'ct': ct,
                        'body_length': len(body),
                        'body_preview': body[:500] if len(body) < 5000 else body[:200],
                    })
                except:
                    api_calls.append({'url': url, 'status': response.status, 'ct': ct})
        
        page.on('response', on_response)
        
        print("Navigating to vidrama.asia/provider/melolo...")
        await page.goto('https://vidrama.asia/provider/melolo', timeout=60000)
        print("Page loaded. Waiting 10s for JS hydration...")
        await page.wait_for_timeout(10000)
        
        # Check what's on the page
        content = await page.content()
        print(f"\nPage content length: {len(content)}")
        
        # Find any drama-related links
        links = await page.query_selector_all('a')
        drama_links = []
        for link in links:
            href = await link.get_attribute('href') or ''
            if '/drama/' in href or '/watch/' in href:
                text = ''
                try:
                    text = (await link.inner_text()).strip()[:60]
                except:
                    pass
                drama_links.append({'href': href, 'text': text})
        
        print(f"\nDrama/watch links found: {len(drama_links)}")
        for dl in drama_links[:10]:
            print(f"  {dl['text']}: {dl['href']}")
        
        # All images on page
        imgs = await page.query_selector_all('img')
        print(f"\nImages on page: {len(imgs)}")
        for img in imgs[:5]:
            src = await img.get_attribute('src') or ''
            alt = await img.get_attribute('alt') or ''
            print(f"  {alt[:30]}: {src[:80]}")
        
        # API calls captured
        print(f"\nAPI calls captured: {len(api_calls)}")
        for ac in api_calls:
            print(f"  [{ac['status']}] {ac['url'][:100]}")
            if 'body_preview' in ac:
                print(f"        {ac['body_preview'][:150]}")
        
        # Save for analysis
        with open('vidrama_debug.json', 'w', encoding='utf-8') as f:
            json.dump({
                'drama_links': drama_links,
                'api_calls': api_calls,
                'page_content_length': len(content),
            }, f, indent=2, ensure_ascii=False)
        
        print("\nSaved: vidrama_debug.json")
        
        # Wait so user can see
        await page.wait_for_timeout(5000)
        await browser.close()

asyncio.run(main())
