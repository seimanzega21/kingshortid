from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://vidrama.asia/provider/netshortv2', wait_until='networkidle')
    time.sleep(2)
    
    # Extract text from all h3 or a tags
    items = page.evaluate('''() => {
        return Array.from(document.querySelectorAll('a')).map(a => {
            return {text: a.innerText, href: a.href}
        });
    }''')
    
    print(f"Found {len(items)} links")
    for item in items:
        text = item['text'].strip()
        if len(text) > 3:
            print(f"{text} -> {item['href']}")
            
    browser.close()
