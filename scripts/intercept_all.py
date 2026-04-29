"""
Intercept ALL API calls on drama detail page to find stream URL.
"""
from playwright.sync_api import sync_playwright
import time
import json

DRAMA_URL = "https://vidrama.asia/movie/pemilik-kitab-pedang--2036690458087784450?provider=netshortv2&lang=id_ID"

def intercept_movie_page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        def handle_response(response):
            url = response.url
            content_type = response.headers.get('content-type', '')
            if 'application/json' in content_type or 'netshortv2' in url or 'netshort' in url:
                print(f"\nAPI [{response.status}]: {url}")
                try:
                    data = response.json()
                    print(f"Data: {json.dumps(data, ensure_ascii=False)[:800]}")
                except:
                    pass
        
        page.on("response", handle_response)
        print(f"Navigating to: {DRAMA_URL}")
        page.goto(DRAMA_URL, wait_until='domcontentloaded')
        time.sleep(8)
        
        # Click play button
        try:
            page.evaluate("window.scrollTo(0, 500)")
            time.sleep(2)
        except:
            pass
        
        browser.close()

intercept_movie_page()
