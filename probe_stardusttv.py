# -*- coding: utf-8 -*-
"""
Probe: Capture m3u8 URLs for multiple episodes to understand URL pattern
and get total episode count for "Satu Pedang, Tebas Raja Neraka"
"""
import asyncio
import json
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

DRAMA_SLUG = 'satu-pedang-tebas-raja-neraka'
DRAMA_ID = '19820'
PROVIDER = 'stardusttv'

async def get_episode_url(page, ep_no):
    """Visit watch page and capture m3u8 URL"""
    url = f'https://vidrama.asia/watch/{DRAMA_SLUG}--{DRAMA_ID}/{ep_no}?provider={PROVIDER}'
    m3u8_captured = []
    
    async def on_request(request):
        rurl = request.url
        if '.m3u8' in rurl or 'stardust' in rurl.lower():
            m3u8_captured.append(rurl)
    
    page.on('request', on_request)
    
    try:
        await page.goto(url, wait_until='networkidle', timeout=30000)
        await asyncio.sleep(3)
    except Exception as e:
        print(f"  EP {ep_no}: Navigation error: {e}")
    
    page.remove_listener('request', on_request)
    
    m3u8_urls = [u for u in m3u8_captured if '.m3u8' in u]
    return m3u8_urls[0] if m3u8_urls else None

async def probe():
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        )
        page = await ctx.new_page()
        
        # Step 1: Get drama metadata from movie page
        print("=== STEP 1: Get Drama Metadata ===")
        movie_url = f'https://vidrama.asia/movie/{DRAMA_SLUG}--{DRAMA_ID}?provider={PROVIDER}'
        
        meta_captured = {}
        
        async def on_response(response):
            url = response.url
            # Capture all relevant API responses
            if 'vidrama.asia' in url and ('movie' in url or 'drama' in url or 'episode' in url):
                try:
                    if 'json' in response.headers.get('content-type', ''):
                        body = await response.json()
                        meta_captured[url] = body
                except:
                    pass
        
        page.on('response', on_response)
        await page.goto(movie_url, wait_until='networkidle', timeout=30000)
        await asyncio.sleep(3)
        page.remove_listener('response', on_response)
        
        # Extract from HTML
        html = await page.content()
        
        # Find total episodes from HTML
        ep_count_match = re.findall(r'(\d+)\s*(?:Episode|Eps|episode)', html)
        print(f"Episode count mentions in HTML: {ep_count_match[:10]}")
        
        # Find description
        desc_match = re.search(r'<meta name="description" content="([^"]+)"', html)
        if desc_match:
            print(f"Description: {desc_match.group(1)[:300]}")
        
        # Find title
        title_match = re.search(r'<title>([^<]+)</title>', html)
        if title_match:
            print(f"Title: {title_match.group(1)}")
        
        # Check captured metadata
        print(f"\nCaptured API responses: {list(meta_captured.keys())[:10]}")
        for url, body in meta_captured.items():
            print(f"\n--- {url} ---")
            print(json.dumps(body, indent=2, ensure_ascii=False)[:500])
        
        # Step 2: Capture m3u8 URLs for episodes 1, 2, 3 to understand pattern
        print("\n=== STEP 2: Probe Episode URLs (EP 1-3) ===")
        for ep_no in [1, 2, 3]:
            m3u8 = await get_episode_url(page, ep_no)
            if m3u8:
                print(f"EP {ep_no}: {m3u8}")
            else:
                print(f"EP {ep_no}: FAILED to capture m3u8")
        
        # Also look at the page HTML for ep list
        print("\n=== STEP 3: Check Episode List HTML ===")
        watch_url = f'https://vidrama.asia/watch/{DRAMA_SLUG}--{DRAMA_ID}/1?provider={PROVIDER}'
        await page.goto(watch_url, wait_until='networkidle', timeout=30000)
        await asyncio.sleep(3)
        html = await page.content()
        
        # Find episode list
        ep_links = re.findall(rf'/watch/{DRAMA_SLUG}--{DRAMA_ID}/(\d+)', html)
        ep_numbers = sorted(set(int(x) for x in ep_links))
        print(f"Episodes found in HTML: {ep_numbers}")
        print(f"Total episodes from HTML: {max(ep_numbers) if ep_numbers else 0}")
        
        await browser.close()

asyncio.run(probe())
