from playwright.sync_api import sync_playwright
import time

def extract_video_src():
    print("Starting playwright...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        def handle_request(request):
            if 'watch' in request.url and request.method == 'POST':
                print(f"POST to Server Action: {request.url}")
            if '.m3u8' in request.url:
                print(f"Found M3U8: {request.url}")
                
        page.on("request", handle_request)
        
        print("Navigating to page...")
        page.goto('https://vidrama.asia/watch/kiamat-datang-aku-beli-istri--31001700648/1?provider=goodshortv2&lang=in', timeout=30000)
        
        page.wait_for_selector('video', timeout=15000)
        time.sleep(3)
        src = page.evaluate("() => document.querySelector('video').src")
        print("Video src attribute:", src)
        
        # If it's a blob, maybe we can find the URL in the window object or local storage
        # Next.js Server Actions inject responses into the page
        
        browser.close()

if __name__ == "__main__":
    extract_video_src()
