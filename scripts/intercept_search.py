from playwright.sync_api import sync_playwright
import time

def intercept():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        def handle_response(response):
            if 'application/json' in response.headers.get('content-type', ''):
                print(f'API: {response.url}')
                try:
                    data = response.json()
                    if isinstance(data, dict) and 'dramas' in data:
                        print(f'   -> found {len(data.get("dramas",[]))} dramas')
                except:
                    pass

        page.on('response', handle_response)
        page.goto('https://vidrama.asia/provider/netshortv2', wait_until='networkidle')
        time.sleep(2)
        
        # Click on search button and type
        page.locator('input[type="text"]').fill('Pedang')
        page.keyboard.press('Enter')
        time.sleep(5)
        
        browser.close()

intercept()
