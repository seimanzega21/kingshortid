import asyncio
from playwright.async_api import async_playwright
import json

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # We will capture all responses
        requests_seen = []
        
        page.on("response", lambda response: requests_seen.append({
            'url': response.url,
            'status': response.status,
            'type': response.request.resource_type
        }))
        
        url = "https://vidrama.asia/watch/dewa-petir-sss-tersembunyi--2089169768653586433/1?provider=netshortv2&lang=id_ID"
        print(f"Loading {url}...")
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=20000)
            await page.wait_for_timeout(3000) # wait a bit more for dynamic stuff
        except Exception as e:
            print(f"Timeout or error: {e}")
        
        print(f"Captured {len(requests_seen)} requests.")
        
        # Filter for interesting ones
        api_reqs = [r for r in requests_seen if 'api' in r['url'] or 'm3u8' in r['url'] or 'vtt' in r['url'] or 'netshort' in r['url']]
        
        print("\nInteresting Requests:")
        for r in api_reqs:
            print(f"[{r['status']}] {r['type']} - {r['url']}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
