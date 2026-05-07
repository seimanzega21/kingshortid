from playwright.sync_api import sync_playwright
import time

def check_html():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('https://vidrama.asia/movie/romantis-di-musim-dingin--1894650560457961473?provider=netshortv2', wait_until='networkidle')
        time.sleep(5)
        
        # Get all buttons or links that might be episodes
        elements = page.query_selector_all('button, a, div[role="button"]')
        for i, el in enumerate(elements):
            text = el.inner_text().strip()
            if text.isdigit():
                print(f"Index {i}: {text}")
        
        browser.close()

if __name__ == "__main__":
    check_html()
