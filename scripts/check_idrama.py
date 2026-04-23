from playwright.sync_api import sync_playwright
import time
import json

def check_idrama():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('https://vidrama.asia/provider/idrama', wait_until='networkidle')
        
        # Scroll down a few times to load lazy content
        for _ in range(5):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(1)
            
        # Try to find drama links. On vidrama, usually it's /drama/something
        # Using a simple css selector: a
        links = page.locator('a').element_handles()
        dramas = set()
        
        for link in links:
            href = link.get_attribute('href')
            if href and ('/drama/' in href or href.startswith('/video/')):
                dramas.add(href)
                
        print(f"Found {len(dramas)} unique dramas by inspecting links.")
        
        # Alternatively, check next.js __NEXT_DATA__
        next_data_elem = page.locator('#__NEXT_DATA__')
        if next_data_elem.count() > 0:
            next_data = next_data_elem.inner_text()
            try:
                data = json.loads(next_data)
                # Next.js 13+ app router doesn't use __NEXT_DATA__ usually.
                print("Found NEXT_DATA. App Router might be different.")
            except Exception as e:
                print("Error parsing next data:", e)
        else:
            print("No __NEXT_DATA__ found. It might be App Router.")
            
        print("Here are some examples:")
        for i, d in enumerate(list(dramas)[:5]):
            print(f"{i+1}. {d}")
            
        browser.close()

if __name__ == "__main__":
    check_idrama()
