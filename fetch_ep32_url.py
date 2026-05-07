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
        
        url = 'https://vidrama.asia/api/netshortv2/movie/1894650560457961473?lang=id_ID'
        print(f"Visiting: {url}")
        await page.goto(url)
        await asyncio.sleep(2)
        content = await page.inner_text("body")
        print("API Response received.")
        
        try:
            data = json.loads(content)
            episodes = data.get('data', {}).get('episodes', [])
            print(f"Episodes: {len(episodes)}")
            ep32 = next((ep for ep in episodes if ep.get('order') == 32), None)
            if ep32:
                print(f"EP32 DATA: {json.dumps(ep32, indent=2)}")
                video_id = ep32.get('id')
                
                # Get stream URL
                stream_url = f"https://vidrama.asia/api/netshortv2/episode/{video_id}?lang=id_ID"
                print(f"Visiting stream API: {stream_url}")
                await page.goto(stream_url)
                await asyncio.sleep(2)
                stream_content = await page.inner_text("body")
                stream_data = json.loads(stream_content)
                video_url = stream_data.get('data', {}).get('video_url')
                print(f"RESULT_VIDEO_URL: {video_url}")
            else:
                print("EP32 not found in episodes list.")
        except Exception as e:
            print(f"Error: {e}")
            print(f"Content start: {content[:200]}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
