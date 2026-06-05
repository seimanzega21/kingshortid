# -*- coding: utf-8 -*-
import sys
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

def test():
    print("Launching Playwright...")
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir='d:/kingshortid/scripts/melolo-scraper/vidrama_profile',
            headless=True
        )
        page = context.new_page()
        print("Visiting vidrama.asia...")
        page.goto("https://vidrama.asia/")
        page.wait_for_timeout(2000)
        
        cookies_list = context.cookies()
        print(f"Total cookies retrieved: {len(cookies_list)}")
        cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies_list])
        print("Cookie String (truncated):", cookie_str[:150])
        
        # Verify checking an API endpoint with the cookie
        print("Testing API fetch...")
        page.goto("https://vidrama.asia/api/netshortv2/detail/2057303745779732481?lang=id_ID")
        page.wait_for_timeout(1000)
        content = page.inner_text("body")
        print("API Response Content length:", len(content))
        print("Content sample:", content[:150])
        
        context.close()

if __name__ == "__main__":
    test()
