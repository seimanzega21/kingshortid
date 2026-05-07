from playwright.sync_api import sync_playwright
import time
import json

def capture_api():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        captured_data = None
        
        def handle_response(response):
            nonlocal captured_data
            # print(f"RES: {response.url[:100]} | {response.status}")
            if "api" in response.url:
                try:
                    if "movie" in response.url:
                        captured_data = response.json()
                        print(f"CAPTURED API DATA from {response.url}")
                except:
                    pass

        page.on("response", handle_response)
        
        url = 'https://vidrama.asia/movie/romantis-di-musim-dingin--1894650560457961473?provider=netshortv2'
        print(f"Navigating to {url}...")
        page.goto(url, wait_until='networkidle')
        time.sleep(10)
        
        if captured_data:
            with open('captured_drama.json', 'w') as f:
                json.dump(captured_data, f, indent=2)
            print("Saved captured data to captured_drama.json")
            
            episodes = captured_data.get('data', {}).get('episodes', [])
            ep32 = next((ep for ep in episodes if ep.get('order') == 32), None)
            if ep32:
                print("Episode 32 found!")
                print(json.dumps(ep32, indent=2))
            else:
                print("Episode 32 not in the captured data")
        else:
            print("No API data captured")
            
        browser.close()

if __name__ == "__main__":
    capture_api()
