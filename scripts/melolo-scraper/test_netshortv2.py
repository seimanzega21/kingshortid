import asyncio, json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        requests_data = []
        
        page.on('response', lambda res: requests_data.append({
            'url': res.url,
            'status': res.status,
            'type': res.request.resource_type
        }))
        
        await page.goto('https://vidrama.asia/provider/netshortv2', wait_until='networkidle')
        
        with open('requests.json', 'w') as f:
            json.dump(requests_data, f, indent=2)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
