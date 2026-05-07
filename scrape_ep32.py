from playwright.sync_api import sync_playwright
import time
import json

def scrape():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print("Navigating to page...")
        page.goto('https://vidrama.asia/movie/romantis-di-musim-dingin--1894650560457961473?provider=netshortv2', wait_until='networkidle')
        time.sleep(5)
        
        # Try to find episode 32
        print("Looking for episode 32...")
        
        # We can also check the __NEXT_DATA__
        next_data_text = page.locator('#__NEXT_DATA__').text_content()
        if next_data_text:
            data = json.loads(next_data_text)
            movie = data.get('props', {}).get('pageProps', {}).get('movie', {})
            episodes = movie.get('episodes', [])
            print(f"Found {len(episodes)} episodes in NEXT_DATA")
            
            ep32 = next((ep for ep in episodes if ep.get('order') == 32), None)
            if ep32:
                print("Episode 32 found in NEXT_DATA!")
                print(json.dumps(ep32, indent=2))
                
                # If we need the stream URL, we might need to click it and intercept network
                # or it might be in the data
            else:
                print("Episode 32 NOT found in NEXT_DATA")
        else:
            print("__NEXT_DATA__ not found")
            
        browser.close()

if __name__ == "__main__":
    scrape()
