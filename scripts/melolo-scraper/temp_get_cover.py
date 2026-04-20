import asyncio
from playwright.async_api import async_playwright

async def get_cover():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={'width': 1280, 'height': 800}, user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36')
        
        url = 'https://vidrama.asia/movie/demi-ada-di-sisimu--2043863926390652929?provider=netshort&lang=in'
        await page.goto(url, wait_until='networkidle', timeout=60000)
        
        # Extract og:image
        cover_url = await page.evaluate('''() => {
            let og = document.querySelector('meta[property="og:image"]');
            if(og && og.content) return og.content;
            let img = document.querySelector('img');
            return img ? img.src : null;
        }''')
        print(f'COVER_URL={cover_url}')
        await browser.close()

asyncio.run(get_cover())
