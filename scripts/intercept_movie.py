"""
Intercept real browser API calls on drama detail page to find stream URL.
"""
from playwright.sync_api import sync_playwright
import time
import json

DRAMA_URL = "https://vidrama.asia/movie/pemilik-kitab-pedang--2036690458087784450?provider=netshortv2&lang=id_ID"

def intercept_movie_page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        api_calls = []
        
        def handle_response(response):
            if 'application/json' in response.headers.get('content-type', ''):
                url = response.url
                if any(x in url for x in ['netshortv2', 'stream', 'play', 'video', 'episode']):
                    print(f"\nAPI: {url}")
                    try:
                        data = response.json()
                        print(f"Data: {json.dumps(data, ensure_ascii=False)[:600]}")
                        api_calls.append({'url': url, 'data': data})
                    except:
                        pass
        
        page.on("response", handle_response)
        print(f"Navigating to: {DRAMA_URL}")
        page.goto(DRAMA_URL, wait_until='domcontentloaded')
        time.sleep(5)
        
        # Click episode 1 if available
        try:
            page.locator('text=Episode 1').first.click()
            time.sleep(3)
        except:
            pass
        
        browser.close()
        return api_calls

intercept_movie_page()
