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
        
        movie_data = None
        
        async def handle_response(response):
            nonlocal movie_data
            if "api/netshortv2/movie/1894650560457961473" in response.url:
                try:
                    movie_data = await response.json()
                except: pass

        page.on("response", handle_response)
        
        # Go to the movie page, it should trigger the movie detail API
        await page.goto('https://vidrama.asia/movie/romantis-di-musim-dingin--1894650560457961473?provider=netshortv2', wait_until='networkidle')
        await asyncio.sleep(5)
        
        if movie_data:
            episodes = movie_data.get('data', {}).get('episodes', [])
            ep32 = next((ep for ep in episodes if ep.get('order') == 32), None)
            if ep32:
                video_id = ep32.get('id')
                print(f"FOUND VIDEO_ID: {video_id}")
                
                # Now try to get the stream URL for this video_id
                stream_api_url = f"https://vidrama.asia/api/netshortv2/episode/{video_id}?lang=id_ID"
                print(f"Fetching stream API: {stream_api_url}")
                
                # Navigate to the stream API URL directly in the browser to bypass protection
                await page.goto(stream_api_url)
                await asyncio.sleep(3)
                content = await page.inner_text("body")
                try:
                    stream_data = json.loads(content)
                    video_url = stream_data.get('data', {}).get('video_url')
                    print(f"STREAM_URL: {video_url}")
                except Exception as e:
                    print(f"Failed to parse stream data: {e}\nContent: {content[:200]}")
            else:
                print("Episode 32 not found in movie data")
        else:
            print("Movie API not captured")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
