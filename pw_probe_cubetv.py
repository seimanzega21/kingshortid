from playwright.sync_api import sync_playwright
import time

def check_post():
    print("Starting playwright...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        def handle_request(request):
            if 'watch' in request.url and request.method == 'POST':
                print(f"POST URL: {request.url}")
                print(f"Headers: {request.headers.get('next-action', 'None')}")
                print(f"Post Data: {request.post_data}")
                
        def handle_response(response):
            if 'watch' in response.url and response.request.method == 'POST':
                print(f"Response from {response.url}:")
                try:
                    print(response.text()[:300])
                except:
                    print("Could not read response text")
                
        page.on("request", handle_request)
        page.on("response", handle_response)
        
        print("Navigating to page...")
        try:
            page.goto('https://vidrama.asia/watch/raja-jalan-raya--NZXDNZ/1?provider=cubetv&lang=id', wait_until='domcontentloaded', timeout=30000)
            time.sleep(10)
        except Exception as e:
            print(e)
            
        browser.close()

if __name__ == "__main__":
    check_post()
