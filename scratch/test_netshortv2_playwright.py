import asyncio
import json
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir='d:/kingshortid/scripts/melolo-scraper/vidrama_profile', 
            headless=True
        )
        page = await browser.new_page()
        
        url = 'https://vidrama.asia/api/netshortv2/movie/1911725995618156546?lang=id_ID'
        print(f"Visiting: {url}")
        await page.goto(url)
        await asyncio.sleep(2)
        content = await page.inner_text("body")
        print("API Response received.")
        
        try:
            data = json.loads(content)
            if data.get('code') == 200:
                movie = data.get('data', {})
                print("Title:", movie.get('title'))
                episodes = movie.get('episodes', [])
                print(f"Episodes count: {len(episodes)}")
                if episodes:
                    print("First ep order/id:", episodes[0].get('order'), episodes[0].get('id'))
            else:
                print("Failed response:", content[:300])
        except Exception as e:
            print(f"Error: {e}")
            print(f"Content: {content[:200]}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
