import asyncio
import json
import re
from playwright.async_api import async_playwright

DRAMA_ID = '21435'
TOTAL_EPS = 61
BASE_URL = 'https://vidrama.asia/id/watch/kakakku-bos-mafia--21435'

async def main():
    captured = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        )
        page = await context.new_page()

        # Intercept API responses for stardusttv
        async def handle_response(response):
            url = response.url
            if 'stardusttv' in url and ('detail' in url or 'episode' in url or 'stream' in url):
                try:
                    body = await response.json()
                    if body.get('success') and body.get('data'):
                        data = body['data']
                        if 'list' in data:
                            print(f'[intercept] Got drama detail with {len(data["list"])} eps')
                            captured['metadata'] = data
                        elif 'videoUrl' in data or 'h264' in data:
                            ep_no = data.get('episodeNo') or data.get('episodeNumber', '?')
                            m3u8 = data.get('h264') or data.get('videoUrl', '')
                            captured[str(ep_no)] = m3u8
                            print(f'[intercept] EP {ep_no}: {m3u8[:80]}')
                except:
                    pass

        page.on('response', handle_response)

        # Visit episode 1
        print(f'Loading ep1...')
        try:
            await page.goto(f'{BASE_URL}/1?provider=stardusttv&lang=id', wait_until='networkidle', timeout=30000)
        except Exception as e:
            print(f'Page load warning: {e}')

        await asyncio.sleep(3)

        # Check what we got
        print(f'Captured keys: {list(captured.keys())[:5]}')

        if 'metadata' in captured:
            meta = captured['metadata']
            episodes = meta.get('list', [])
            print(f'Title: {meta.get("title")}')
            print(f'Episodes: {len(episodes)}')
            # Save to file
            with open('kakakku_bos_mafia_episodes.json', 'w', encoding='utf-8') as f:
                json.dump(episodes, f, indent=2, ensure_ascii=False)
            print('Saved to kakakku_bos_mafia_episodes.json')
        else:
            print('No metadata captured via intercept')
            # Try evaluating the page for any data
            title = await page.title()
            print('Page title:', title)

        await browser.close()

asyncio.run(main())
