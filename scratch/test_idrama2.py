from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        def handle_response(response):
            print(f"URL: {response.url}")
                    
        page.on("response", handle_response)
        
        page.goto('https://vidrama.asia/movie/sang-ceo-dan-tunangan-cleaning-service-nya--160000643080?provider=idrama2&lang=id', wait_until='networkidle')
        
        browser.close()

if __name__ == '__main__':
    run()
