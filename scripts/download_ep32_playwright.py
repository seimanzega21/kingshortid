import asyncio
from playwright.async_api import async_playwright
from pathlib import Path
import requests

PROFILE_DIR = Path("d:/kingshortid/scripts/melolo-scraper/vidrama_profile")

async def download_ep32():
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            headless=True
        )
        page = await browser.new_page()
        
        # Go to the episode page to trigger session/headers
        print("Opening Vidrama...")
        await page.goto("https://vidrama.asia/netshortv2/2021413378848690178/32")
        await asyncio.sleep(5)
        
        # Get the video URL from the page
        vurl = await page.evaluate('''() => {
            const video = document.querySelector('video');
            return video ? video.src : null;
        }''')
        
        print(f"Video URL from page: {vurl}")
        
        if vurl:
            # Try to download using page.request (shares session)
            print("Downloading via Playwright request...")
            response = await page.request.get(vurl)
            if response.status == 200:
                with open("ep32_raw.mp4", "wb") as f:
                    f.write(await response.body())
                print("Download SUCCESS!")
            else:
                print(f"Download FAILED: {response.status}")
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(download_ep32())
