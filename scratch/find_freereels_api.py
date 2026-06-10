from playwright.sync_api import sync_playwright
import json

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
    page = context.new_page()

    def handle_response(response):
        if 'api' in response.url or 'search' in response.url or 'list' in response.url:
            print(f"API Response: {response.url} ({response.status})")
            if 'image' not in response.headers.get('content-type', ''):
                try:
                    body = response.body()
                    if body and b'{' in body:
                        data = json.loads(body)
                        if 'data' in data or 'results' in data or 'items' in data:
                            print(f"  -> Found data object with keys: {list(data.keys())}")
                            # Inspect items
                            items = data.get('data', data.get('results', data.get('items', [])))
                            if isinstance(items, list) and len(items) > 0:
                                print(f"  -> First item: {str(items[0])[:200]}")
                except Exception as e:
                    pass

    page.on("response", handle_response)
    print("Navigating to https://vidrama.asia/provider/freereels...")
    page.goto("https://vidrama.asia/provider/freereels", wait_until="networkidle")
    print("Page title:", page.title())
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
