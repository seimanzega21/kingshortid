from playwright.sync_api import sync_playwright
import time
import json

def scrape_ep32():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Use a real user agent
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        video_url = None
        
        def handle_request(request):
            nonlocal video_url
            # Print all requests for debugging
            # print(f"REQ: {request.url[:100]}")
            if "awscdn.netshort.com" in request.url:
                video_url = request.url
                print(f"CAPTURED VIDEO URL: {video_url}")

        page.on("request", handle_request)
        
        url = 'https://vidrama.asia/movie/romantis-di-musim-dingin--1894650560457961473?provider=netshortv2'
        print(f"Navigating to {url}...")
        page.goto(url, wait_until='networkidle')
        time.sleep(5)
        
        # Try to find episode 32 button and click it
        print("Looking for episode 32 button...")
        # Episode buttons usually have the episode number as text
        # Let's try to find a button or div with text "32"
        try:
            # We might need to scroll or wait
            ep32_button = page.get_by_text("32", exact=True)
            if ep32_button.is_visible():
                print("Clicking episode 32...")
                ep32_button.click()
                time.sleep(10) # Wait for video to start
            else:
                print("Episode 32 button not visible, trying to find all buttons...")
                # Maybe it's in a list. Let's try to find elements that look like episode selectors
                page.screenshot(path="debug_page.png")
                print("Saved screenshot to debug_page.png")
        except Exception as e:
            print(f"Error clicking episode 32: {e}")
            
        browser.close()
        return video_url

if __name__ == "__main__":
    url = scrape_ep32()
    if url:
        print(f"\nSUCCESS: Episode 32 Video URL: {url}")
    else:
        print("\nFAILED: Could not capture video URL for episode 32")
