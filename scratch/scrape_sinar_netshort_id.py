from playwright.sync_api import sync_playwright
import time
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with sync_playwright() as p:
    print("Launching browser...")
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()
    
    print("Navigating to https://vidrama.asia/provider/netshortv2 ...")
    page.goto('https://vidrama.asia/provider/netshortv2', wait_until='networkidle')
    time.sleep(5)
    
    print("Locating #__NEXT_DATA__ ...")
    try:
        next_data_text = page.locator('#__NEXT_DATA__').text_content()
        data = json.loads(next_data_text)
        dramas = data.get('props', {}).get('pageProps', {}).get('dramas', [])
        print(f"Found {len(dramas)} dramas in NEXT_DATA")
        
        found = False
        for d in dramas:
            title = d.get('title', '')
            if 'sinar' in title.lower() or 'mencari' in title.lower():
                print(f"FOUND: {title} -> ID: {d.get('id')} | Cover: {d.get('cover')}")
                found = True
        
        if not found:
            print("Listing all dramas in the page:")
            for d in dramas:
                print(f"  - {d.get('title')} (ID: {d.get('id')})")
                
    except Exception as e:
        print("Error:", e)
        
    browser.close()
