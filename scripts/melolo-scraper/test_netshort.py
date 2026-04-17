import asyncio
import re
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://vidrama.asia/provider/netshort", timeout=30000)
        
        # Scroll more to get everything
        for _ in range(25):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)
            
        html = await page.content()
        
        script = """
        () => {
            const links = Array.from(document.querySelectorAll('a[href*="/movie/"]'));
            const results = [];
            for (const a of links) {
                const href = a.getAttribute('href');
                const match = href.match(/\\/movie\\/([a-z0-9-]+)--(\\d{15,})/);
                if (match) {
                    const img = a.querySelector('img');
                    let title = "";
                    let cover = "";
                    if (img) {
                        cover = img.src || "";
                        title = img.alt || "";
                    }
                    if (!title) {
                        title = match[1].split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
                    }
                    results.push({
                        slug: match[1],
                        id: match[2],
                        title: title,
                        cover_url: cover
                    });
                }
            }
            return results;
        }
        """
        scraped_dramas = await page.evaluate(script)
        print(f"Total dramas found on provider page: {len(scraped_dramas)}")
        
        bandit = [d for d in scraped_dramas if 'bandit' in d['slug']]
        if bandit:
            print(f"Found Bandit: {bandit[0]}")
        else:
            print("Bandit not found in standard scroll.")
            
        await browser.close()

asyncio.run(run())
