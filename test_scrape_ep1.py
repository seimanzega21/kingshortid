# -*- coding: utf-8 -*-
"""Quick test: Cek apakah scraper bisa capture EP 1 dan download dengan benar"""
import asyncio
import subprocess
import sys
import os
import time

sys.stdout.reconfigure(encoding='utf-8')

DRAMA_SLUG   = 'satu-pedang-tebas-raja-neraka'
DRAMA_ID_WEB = '19820'
PROVIDER     = 'stardusttv'

async def test_ep1():
    from playwright.async_api import async_playwright
    
    m3u8_urls = []
    print("Launching browser...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await ctx.new_page()
        
        async def on_req(req):
            if '.m3u8' in req.url:
                m3u8_urls.append(req.url)
                print(f"  ✅ M3U8 captured: {req.url[-70:]}")
        
        page.on('request', on_req)
        
        watch_url = f'https://vidrama.asia/watch/{DRAMA_SLUG}--{DRAMA_ID_WEB}/1?provider={PROVIDER}'
        print(f"Opening: {watch_url}")
        
        try:
            await page.goto(watch_url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Error: {e}")
        
        await browser.close()
    
    return m3u8_urls[0] if m3u8_urls else None

m3u8 = asyncio.run(test_ep1())

if m3u8:
    print(f"\n✅ EP 1 m3u8: {m3u8}")
    
    # Test quick ffmpeg download (first 30 seconds only)
    out = "D:/kingshortid/temp_raja/test_ep1.mp4"
    os.makedirs("D:/kingshortid/temp_raja", exist_ok=True)
    
    print("\nTesting ffmpeg download (30 sec clip)...")
    hdrs = (
        "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\r\n"
        "Referer: https://vidrama.asia/\r\n"
    )
    cmd = [
        'ffmpeg', '-y',
        '-headers', hdrs,
        '-i', m3u8,
        '-t', '30',
        '-c', 'copy',
        '-movflags', '+faststart',
        '-loglevel', 'warning',
        out
    ]
    t0 = time.time()
    res = subprocess.run(cmd, capture_output=True, text=True, errors='ignore', timeout=60)
    elapsed = time.time() - t0
    
    if res.returncode == 0 and os.path.exists(out):
        size = os.path.getsize(out) / (1024*1024)
        print(f"✅ FFmpeg OK! Size: {size:.2f} MB, Time: {elapsed:.1f}s")
    else:
        print(f"❌ FFmpeg FAILED: {res.stderr[-500:]}")
else:
    print("❌ Failed to capture m3u8 URL!")
