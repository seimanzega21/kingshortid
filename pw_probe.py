from playwright.sync_api import sync_playwright
import time

def scrape_video_url():
    print("Starting playwright...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        video_url = None
        
        def handle_response(response):
            nonlocal video_url
            if '/api/goodshort/stream' in response.url:
                print(f"API Response: {response.status} {response.url}")
                try:
                    data = response.json()
                    if 'videoUrl' in data:
                        video_url = data['videoUrl']
                        print(f"Found videoUrl: {video_url}")
                    else:
                        print("Response json:", data)
                except Exception as e:
                    print("Error parsing json:", e)
        
        page.on("response", handle_response)
        
        print("Navigating to page...")
        try:
            page.goto('https://vidrama.asia/watch/kiamat-datang-aku-beli-istri--31001700648/1?provider=goodshortv2&lang=in', timeout=30000)
            page.wait_for_selector('video', timeout=15000)
            print("Video tag found!")
        except Exception as e:
            print("Timeout or error:", e)
            print("Page title:", page.title())
            
        time.sleep(3)
        browser.close()
        return video_url

if __name__ == "__main__":
    scrape_video_url()
