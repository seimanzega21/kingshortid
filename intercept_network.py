# -*- coding: utf-8 -*-
import sys, json
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

def main():
    url = 'https://vidrama.asia/id/watch/reinkarnasi-pilot-ulung--7653295748544465973/1?provider=melolov3'
    print(f"Launching playwright to open: {url}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        requests_logged = []
        page.on("request", lambda req: requests_logged.append(req))
        
        responses_logged = []
        page.on("response", lambda res: responses_logged.append(res))
        
        try:
            page.goto(url, wait_until='networkidle', timeout=30000)
            print("Page loaded successfully.")
        except Exception as e:
            print("Error loading page:", e)
            
        print(f"\nTotal requests: {len(requests_logged)}")
        print(f"Total responses: {len(responses_logged)}")
        
        print("\nAll Requests (first 50):")
        for req in requests_logged[:50]:
            print(f"  {req.method} | {req.url}")
            
        print("\nAll Responses (first 50):")
        for res in responses_logged[:50]:
            print(f"  {res.status} | {res.url}")
            
        browser.close()

if __name__ == "__main__":
    main()
