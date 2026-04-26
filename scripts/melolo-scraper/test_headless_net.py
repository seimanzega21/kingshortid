import asyncio
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context('d:/kingshortid/scripts/melolo-scraper/vidrama_profile', headless=True)
        page = await browser.new_page()
        
        async def handle_response(res):
            if 'm3u8' in res.url or res.request.method == 'POST':
                print('RES:', res.url)
                if res.request.method == 'POST':
                    try:
                        text = await res.text()
                        print('   BODY:', text[:200])
                    except:
                        pass
                        
        page.on('response', handle_response)
        print("Navigating...")
        await page.goto('https://vidrama.asia/watch/dubbingsopir-taksi-mantan-dewa-balap--846959/1?provider=shortmax', wait_until='networkidle')
        await asyncio.sleep(5)
        await browser.close()

asyncio.run(test())
