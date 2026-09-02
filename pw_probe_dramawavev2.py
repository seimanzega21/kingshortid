from playwright.sync_api import sync_playwright
import time

def check_network():
    print("Starting playwright...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        def handle_request(request):
            if 'vidrama.asia/api/' in request.url or 'dramawave' in request.url:
                print(f"Req: {request.method} {request.url}")
                
        page.on("request", handle_request)
        
        print("Navigating to movie page...")
        try:
            page.goto('https://vidrama.asia/movie/pewaris-terbuang-adalah-penyihir-ilahi--RYPtQ25Q0h?provider=dramawavev2&lang=in', wait_until='domcontentloaded', timeout=30000)
            time.sleep(5)
            
            print("\nNavigating to watch page...")
            page.goto('https://vidrama.asia/watch/pewaris-terbuang-adalah-penyihir-ilahi--RYPtQ25Q0h/1?provider=dramawavev2&lang=in', wait_until='domcontentloaded', timeout=30000)
            time.sleep(5)
        except Exception as e:
            print(e)
            
        browser.close()

if __name__ == "__main__":
    check_network()
