import asyncio
import sys
import json
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        print("[*] Launching browser with persistent context...")
        browser = await p.chromium.launch_persistent_context(
            user_data_dir='d:/kingshortid/scripts/melolo-scraper/vidrama_profile', 
            headless=True,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = await browser.new_page()
        
        video_url = None
        
        async def handle_request(request):
            nonlocal video_url
            if "awscdn.netshort.com" in request.url:
                video_url = request.url
                print(f"[!] CAPTURED VIDEO URL: {video_url}")
                
        page.on("request", handle_request)
        
        # We also want to capture the API response if possible
        async def handle_response(response):
            if "api/netshortv2/movie" in response.url:
                try:
                    data = await response.json()
                    with open('movie_api_captured.json', 'w') as f:
                        json.dump(data, f, indent=2)
                    print(f"[*] Captured movie API response")
                except: pass

        page.on("response", handle_response)
        
        target_url = 'https://vidrama.asia/watch/romantis-di-musim-dingin--1894650560457961473/32?provider=netshortv2'
        print(f"[*] Navigating to {target_url}...")
        
        try:
            await page.goto(target_url, wait_until='load', timeout=60000)
            print("[*] Page loaded, waiting for video...")
            await asyncio.sleep(10)
            await page.screenshot(path="vidrama_watch.png")
            print("[*] Screenshot saved to vidrama_watch.png")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"[X] Error: {e}")
            
        await browser.close()
        return video_url

if __name__ == "__main__":
    result = asyncio.run(run())
    if result:
        print(f"\nFINAL VIDEO URL: {result}")
    else:
        print("\nFAILED to capture video URL")
