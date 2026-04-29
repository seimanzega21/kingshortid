"""
Parse RSC (React Server Component) data from the /watch endpoint to extract video URLs.
"""
from playwright.sync_api import sync_playwright
import time
import json
import re

WATCH_URL = "https://vidrama.asia/watch/pemilik-kitab-pedang--2036690458087784450/1?provider=netshortv2"

def intercept_watch():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        
        video_urls = []
        
        def handle_response(response):
            url = response.url
            content_type = response.headers.get('content-type', '')
            
            if any(x in url for x in ['m3u8', '.mp4', '.webp', 'netshort.com/hls', 'netshort.com/video']):
                print(f"\nVIDEO/MEDIA: {url}")
                video_urls.append(url)
            elif '_rsc' in url and 'watch' in url:
                try:
                    text = response.text()
                    # Extract video URLs from RSC data
                    mp4_matches = re.findall(r'https?://[^\s"]+\.mp4[^\s"]*', text)
                    m3u8_matches = re.findall(r'https?://[^\s"]+\.m3u8[^\s"]*', text)
                    hls_matches = re.findall(r'https?://[^\s"]+/hls[^\s"]*', text)
                    
                    if mp4_matches:
                        print(f"\nMP4 in RSC {url}:")
                        for m in mp4_matches: print(f"  {m}")
                    if m3u8_matches:
                        print(f"\nM3U8 in RSC {url}:")
                        for m in m3u8_matches: print(f"  {m}")
                    if hls_matches:
                        print(f"\nHLS in RSC {url}:")
                        for m in hls_matches: print(f"  {m}")
                        
                    # also look for any video-like field
                    if 'videoUrl' in text or 'playUrl' in text or 'streamUrl' in text:
                        print(f"\nStream field in RSC: {url}")
                        # extract surrounding context
                        for field in ['videoUrl', 'playUrl', 'streamUrl']:
                            idx = text.find(field)
                            if idx >= 0:
                                print(f"  {field}: {text[idx:idx+200]}")
                except:
                    pass
        
        page.on("response", handle_response)
        print(f"Navigating to: {WATCH_URL}")
        page.goto(WATCH_URL, wait_until='domcontentloaded')
        time.sleep(10)
        
        # Get page HTML 
        html = page.content()
        
        # Look for video in source
        mp4 = re.findall(r'https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*', html)
        m3u8 = re.findall(r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*', html)
        if mp4:
            print(f"\nMP4 in page HTML:")
            for u in mp4: print(f"  {u}")
        if m3u8:
            print(f"\nM3U8 in page HTML:")
            for u in m3u8: print(f"  {u}")
            
        browser.close()

intercept_watch()
