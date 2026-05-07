import asyncio
import json
import re
import requests
from playwright.async_api import async_playwright

API_BASE    = 'https://api.shortlovers.id'
ADMIN_KEY   = '00ca04e3e2702be565d7bf44e783255247708289bce9b2fb6187a2e117f87fd14'
ADMIN_HDR   = {'x-admin-key': ADMIN_KEY, 'Content-Type': 'application/json'}

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")

async def scrape_drama(id, title):
    async with async_playwright() as p:
        print(f"\n[*] Processing: {title}")
        browser = await p.chromium.launch_persistent_context(
            user_data_dir='d:/kingshortid/scripts/melolo-scraper/vidrama_profile', 
            headless=True
        )
        page = await browser.new_page()
        
        movie_data = None
        async def handle_response(response):
            nonlocal movie_data
            if f"api/netshortv2/movie/{id}" in response.url:
                try: movie_data = await response.json()
                except: pass
        page.on("response", handle_response)

        url = f'https://vidrama.asia/movie/{slugify(title)}--{id}?provider=netshortv2'
        await page.goto(url, wait_until='networkidle')
        await asyncio.sleep(5)
        
        if movie_data and movie_data.get('code') == 200:
            detail = movie_data['data']
            print(f"[+] Captured detail for: {detail['title']}")
            
            # Register Drama
            payload = {
                'title': detail['title'],
                'description': detail.get('description', detail['title']),
                'cover': detail['cover'],
                'genres': detail.get('labels', ['Drama']),
                'totalEpisodes': detail.get('totalEpisodes', 0),
                'status': 'completed' if detail.get('isFinished') else 'ongoing',
                'country': 'China', 'language': 'Indonesia',
                'isActive': False
            }
            r = requests.post(f"{API_BASE}/api/admin/dramas", headers=ADMIN_HDR, json=payload)
            if r.ok:
                db_id = r.json().get('id')
                print(f"[+] Registered Drama DB ID: {db_id}")
                
                # Process first 5 episodes as sample
                episodes = detail.get('episodes', [])
                for ep in episodes[:5]:
                    ep_no = ep.get('order')
                    # We need to click/trigger episode API to get videoUrl
                    # But for now let's just register the episode structure
                    ep_payload = {
                        'episodeNumber': ep_no,
                        'title': f'Episode {ep_no}',
                        'videoUrl': 'https://pending-upload.mp4',
                        'isActive': True
                    }
                    requests.post(f"{API_BASE}/api/admin/dramas/{db_id}/episodes", headers=ADMIN_HDR, json=ep_payload)
                print(f"[+] Registered {min(len(episodes), 5)} episodes structure.")
            else:
                print(f"[-] Failed to register drama: {r.text}")
        else:
            print(f"[-] Failed to capture API data for {id}")
            
        await browser.close()

async def main():
    targets = [
        {"id": "2050068409973997569", "title": "Raja yang Ditakuti Musuh"},
        {"id": "2033798825713336321", "title": "Menghabisi yang Jahat"},
        {"id": "2020778605549871106", "title": "Dua Kuasa Menjadi Satu"}
    ]
    for t in targets:
        await scrape_drama(t['id'], t['title'])

if __name__ == "__main__":
    asyncio.run(main())
