from playwright.sync_api import sync_playwright
import time

def scrape_m3u8():
    print("Starting playwright...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        m3u8_url = None
        
        def handle_request(request):
            nonlocal m3u8_url
            if '.m3u8' in request.url or '.ts' in request.url or 'v3.goodshort.com' in request.url:
                print(f"Detected Stream Request: {request.url}")
                if '.m3u8' in request.url:
                    m3u8_url = request.url
        
        page.on("request", handle_request)
        
        print("Navigating to page...")
        try:
            page.goto('https://vidrama.asia/watch/kiamat-datang-aku-beli-istri--31001700648/1?provider=goodshortv2&lang=in', timeout=30000)
            page.wait_for_selector('video', timeout=15000)
            print("Video tag found!")
        except Exception as e:
            print("Timeout or error:", e)
            
        # Give it a few seconds to load the stream
        time.sleep(5)
        print(f"Final Extracted M3U8: {m3u8_url}")
        browser.close()

if __name__ == "__main__":
    scrape_m3u8()
