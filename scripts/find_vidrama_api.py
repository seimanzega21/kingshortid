from playwright.sync_api import sync_playwright
import time
import json

def listen_api():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        api_urls = []
        
        def handle_response(response):
            if 'application/json' in response.headers.get('content-type', '') or '/api/' in response.url or 'supabase.co' in response.url:
                print(f"API/JSON URL: {response.url}")
                try:
                    data = response.json()
                    # print snippet
                    print("Data snippet:", str(data)[:200])
                except:
                    pass

        page.on("response", handle_response)
        print("Navigating to https://vidrama.asia/provider/idrama...")
        page.goto('https://vidrama.asia/provider/idrama', wait_until='networkidle')
        
        # Scroll to trigger any lazy loads
        for _ in range(3):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
            
        browser.close()

if __name__ == "__main__":
    listen_api()
