from playwright.sync_api import sync_playwright
import time
import json

def listen_api():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        def handle_response(response):
            if '/api/' in response.url:
                print(f"API URL: {response.url}")

        page.on("response", handle_response)
        print("Navigating to https://vidrama.asia/provider/netshortv2...")
        page.goto('https://vidrama.asia/provider/netshortv2', wait_until='networkidle')
        
        # Scroll to trigger any lazy loads
        for _ in range(5):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)
            
        browser.close()

if __name__ == "__main__":
    listen_api()
