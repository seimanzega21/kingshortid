"""
Fetch vidrama watch page via Playwright and extract the video source from the actual player.
Also capture XHR requests to netshort APIs to find the HLS/MP4 URL.
"""
from playwright.sync_api import sync_playwright
import time
import re

WATCH_URL = "https://vidrama.asia/watch/pemilik-kitab-pedang--2036690458087784450/1?provider=netshortv2"

def extract_video_src():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        found_urls = []
        
        def handle_request(request):
            url = request.url
            if any(x in url for x in ['.m3u8', '.mp4', 'netshort.com/hls', 'netshort.com/video', 'vod']):
                print(f"\nVIDEO REQUEST: {url}")
                found_urls.append(url)
        
        def handle_response(response):
            url = response.url
            if any(x in url for x in ['.m3u8', '.mp4', 'netshort.com/hls', 'netshort.com/video', 'vod']):
                print(f"\nVIDEO RESPONSE: {url} [{response.status}]")
            elif 'application/json' in response.headers.get('content-type', ''):
                if any(x in url for x in ['netshortv2', 'episode', 'stream', 'play']) and 'vidrama' in url:
                    try:
                        data = response.json()
                        print(f"\nJSON API: {url}")
                        import json
                        print(f"  {json.dumps(data, ensure_ascii=False)[:500]}")
                    except:
                        pass
        
        page.on("request", handle_request)
        page.on("response", handle_response)
        
        print(f"Navigating to: {WATCH_URL}")
        page.goto(WATCH_URL, wait_until='domcontentloaded')
        time.sleep(3)
        
        # Get all video sources from DOM
        video_srcs = page.evaluate("""() => {
            const videos = document.querySelectorAll('video');
            return Array.from(videos).map(v => ({
                src: v.src,
                currentSrc: v.currentSrc,
            }));
        }""")
        
        print(f"\nVideo elements: {video_srcs}")
        
        # Get inner HTML of player to find embedded URL
        player_html = page.evaluate("""() => {
            const player = document.querySelector('[class*="player"]') || document.querySelector('video');
            return player ? player.outerHTML : 'not found';
        }""")
        print(f"\nPlayer HTML: {player_html[:500]}")
        
        # Check iframes for embedded players
        iframes = page.evaluate("""() => {
            return Array.from(document.querySelectorAll('iframe')).map(f => f.src);
        }""")
        print(f"\nIframes: {iframes}")
        
        # Get full page HTML and find video URLs
        html = page.content()
        mp4 = re.findall(r'https?://[^\s"\'\\<>]+\.mp4[^\s"\'\\<>]*', html)
        m3u8 = re.findall(r'https?://[^\s"\'\\<>]+\.m3u8[^\s"\'\\<>]*', html)
        print(f"\nMP4 in HTML: {mp4}")
        print(f"M3U8 in HTML: {m3u8}")
        
        time.sleep(5)
        
        # Get video src again after potential load
        video_srcs2 = page.evaluate("""() => {
            const videos = document.querySelectorAll('video');
            return Array.from(videos).map(v => ({
                src: v.src,
                currentSrc: v.currentSrc,
            }));
        }""")
        print(f"\nVideo elements (after wait): {video_srcs2}")
        
        browser.close()

extract_video_src()
