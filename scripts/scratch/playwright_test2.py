import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("Navigating...")
        await page.goto('https://vidrama.asia/provider/idrama', wait_until='networkidle')
        print("Waiting 5s...")
        await asyncio.sleep(5)
        
        # Dump HTML body
        html = await page.content()
        with open('d:/kingshortid/scripts/scratch/playwright_vidrama.html', 'w', encoding='utf-8') as f:
            f.write(html)
            
        links = await page.eval_on_selector_all('a', 'elements => elements.map(e => e.href)')
        print(f"Found {len(links)} links")
        
        # Filter drama links (they don't start with /provider or /search)
        drama_links = [l for l in set(links) if 'vidrama.asia' in l and not 'provider' in l and not 'search' in l and not 'login' in l]
        for l in drama_links[:10]:
            print(l)
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
