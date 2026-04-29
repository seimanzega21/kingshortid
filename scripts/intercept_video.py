"""
Intercept ALL API calls including video/HLS URLs on drama page.
"""
from playwright.sync_api import sync_playwright
import time
import json
import re

DRAMA_URL = "https://vidrama.asia/movie/pemilik-kitab-pedang--2036690458087784450?provider=netshortv2&lang=id_ID"

def intercept_movie_page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        def handle_response(response):
            url = response.url
            content_type = response.headers.get('content-type', '')
            # Look for video, HLS, m3u8, or any netshort URLs
            if any(x in url for x in ['m3u8', '.mp4', 'netshort.com/video', 'netshort.com/hls', 'stream']):
                print(f"\nVIDEO URL [{response.status}]: {url}")
            elif 'netshortv2' in url or 'netshort' in url and 'api' in url:
                print(f"\nAPI [{response.status}]: {url}")
                try:
                    data = response.json()
                    print(f"Data: {json.dumps(data, ensure_ascii=False)[:800]}")
                except:
                    pass
        
        def handle_request(request):
            url = request.url
            if any(x in url for x in ['m3u8', '.mp4', 'stream', 'video', 'netshort.com']):
                print(f"\nREQUEST: {url}")
        
        page.on("response", handle_response)
        page.on("request", handle_request)
        
        print(f"Navigating to: {DRAMA_URL}")
        page.goto(DRAMA_URL, wait_until='domcontentloaded')
        
        # Wait and scroll to trigger video load
        time.sleep(5)
        
        # Try clicking on the play area
        try:
            # Find and click the video player/first episode
            vid = page.locator('video').first
            if vid:
                vid.click()
                time.sleep(3)
        except:
            pass
        
        try:
            page.locator('[class*="episode"]').first.click()
            time.sleep(3)
        except:
            pass
        
        time.sleep(5)
        browser.close()

intercept_movie_page()
