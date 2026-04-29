from playwright.sync_api import sync_playwright
import time
import json

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://vidrama.asia/provider/netshortv2', wait_until='networkidle')
    time.sleep(2)
    next_data_text = page.locator('#__NEXT_DATA__').text_content()
    data = json.loads(next_data_text)
    dramas = data.get('props', {}).get('pageProps', {}).get('dramas', [])
    print(f'Found {len(dramas)} dramas in NEXT_DATA')
    for d in dramas:
        title = d.get('title', '')
        if 'Pedang' in title or 'Jenderal' in title or 'Robot' in title:
            print(f'FOUND: {title} -> ID: {d.get("id")}')
    browser.close()
