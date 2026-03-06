#!/usr/bin/env python3
"""
VIDRAMA.ASIA SCRAPER — Phase 1: Discovery
==========================================
Uses Playwright to navigate vidrama.asia/provider/melolo,
discover all dramas and their episode counts, and extract
video source URLs.
"""
import json, asyncio, re, sys
from pathlib import Path
from playwright.async_api import async_playwright


async def discover_dramas(page):
    """Navigate to Melolo provider page and discover all drama links."""
    print("\n=== DISCOVERING DRAMAS ===\n")
    
    await page.goto('https://vidrama.asia/provider/melolo', timeout=60000)
    await page.wait_for_timeout(5000)
    
    # Scroll down to load all dramas (lazy loading)
    prev_count = 0
    stable = 0
    for scroll in range(30):
        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
        await page.wait_for_timeout(2000)
        
        links = await page.query_selector_all('a[href*="/drama/"]')
        count = len(links)
        print(f"  Scroll {scroll+1}: {count} drama links")
        
        if count == prev_count:
            stable += 1
            if stable >= 3:
                break
        else:
            stable = 0
        prev_count = count
    
    # Extract all unique drama URLs
    links = await page.query_selector_all('a[href*="/drama/"]')
    dramas = {}
    for link in links:
        href = await link.get_attribute('href')
        if not href or '/drama/' not in href:
            continue
        slug = href.split('/drama/')[-1].split('?')[0].strip('/')
        if not slug or slug in dramas:
            continue
        
        # Get title from inner text or img alt
        text = ''
        try:
            text = (await link.inner_text()).strip()
        except:
            pass
        if not text or len(text) > 200:
            img = await link.query_selector('img')
            if img:
                text = (await img.get_attribute('alt')) or ''
        if not text:
            text = slug.replace('-', ' ').title()
        
        # Get cover URL
        cover = ''
        img = await link.query_selector('img')
        if img:
            cover = (await img.get_attribute('src')) or ''
        
        dramas[slug] = {
            'slug': slug,
            'title': text.split('\n')[0].strip()[:100],
            'url': f'https://vidrama.asia/drama/{slug}',
            'cover': cover,
        }
    
    print(f"\n  Total unique dramas: {len(dramas)}")
    for s, d in sorted(dramas.items()):
        print(f"    {d['title'][:60]}")
    return dramas


async def get_drama_episodes(page, drama):
    """Get episode list from a drama page."""
    try:
        await page.goto(drama['url'], timeout=30000)
        await page.wait_for_timeout(3000)
        
        # Try to find episode links
        ep_links = await page.query_selector_all('a[href*="/watch/"]')
        
        if not ep_links:
            # Wait a bit more and try again
            await page.wait_for_timeout(3000)
            ep_links = await page.query_selector_all('a[href*="/watch/"]')
        
        episodes = []
        seen_urls = set()
        for link in ep_links:
            href = await link.get_attribute('href') or ''
            if not href or href in seen_urls:
                continue
            seen_urls.add(href)
            text = ''
            try:
                text = (await link.inner_text()).strip()
            except:
                pass
            full_url = href if href.startswith('http') else f'https://vidrama.asia{href}'
            episodes.append({
                'number': len(episodes) + 1,
                'label': text[:30],
                'url': full_url,
            })
        
        # Get description
        desc = ''
        for sel in ['[class*="synopsis"]', '[class*="description"]', '[class*="desc"]', 'p']:
            el = await page.query_selector(sel)
            if el:
                t = (await el.inner_text()).strip()
                if len(t) > 30:
                    desc = t[:500]
                    break
        
        drama['description'] = desc
        drama['episodes'] = episodes
        drama['total_episodes'] = len(episodes)
        return True
        
    except Exception as e:
        drama['error'] = str(e)[:200]
        return False


async def extract_video_url(page, watch_url):
    """Navigate to watch page and capture video source URL."""
    captured = []
    
    async def on_response(response):
        url = response.url
        if any(x in url.lower() for x in ['.mp4', '.m3u8', '/video/', '/stream/', 'playback']):
            captured.append(url)
    
    page.on('response', on_response)
    
    try:
        await page.goto(watch_url, timeout=30000)
        await page.wait_for_timeout(5000)
        
        # Check video element
        video = await page.query_selector('video')
        if video:
            src = await video.get_attribute('src')
            if src:
                captured.append(src)
        
        # Check source elements
        sources = await page.query_selector_all('video source')
        for s in sources:
            src = await s.get_attribute('src')
            if src:
                captured.append(src)
        
        # Try extracting from page JS
        content = await page.content()
        mp4s = re.findall(r'https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*', content)
        m3u8s = re.findall(r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*', content)
        captured.extend(mp4s)
        captured.extend(m3u8s)
        
        # Also check via evaluate
        try:
            js_urls = await page.evaluate('''() => {
                const videos = document.querySelectorAll('video');
                const urls = [];
                videos.forEach(v => {
                    if (v.src) urls.push(v.src);
                    if (v.currentSrc) urls.push(v.currentSrc);
                    v.querySelectorAll('source').forEach(s => {
                        if (s.src) urls.push(s.src);
                    });
                });
                return urls;
            }''')
            captured.extend(js_urls)
        except:
            pass
        
    except Exception as e:
        print(f"      Error: {str(e)[:60]}")
    
    page.remove_listener('response', on_response)
    
    # Deduplicate
    unique = list(dict.fromkeys(captured))
    return unique


async def main():
    print("="*70)
    print("  VIDRAMA.ASIA MELOLO SCRAPER — Discovery")
    print("="*70)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        )
        page = await context.new_page()
        
        # Step 1: Discover all dramas
        dramas = await discover_dramas(page)
        
        # Step 2: Get episode details for first 3 dramas + extract video URL test
        print("\n=== GETTING EPISODE DETAILS (first 3 test) ===\n")
        drama_list = list(dramas.values())
        
        for i, drama in enumerate(drama_list[:3], 1):
            print(f"\n  [{i}/3] {drama['title'][:50]}")
            ok = await get_drama_episodes(page, drama)
            if ok:
                print(f"    Episodes: {drama.get('total_episodes', 0)}")
                
                # Test video extraction on first episode
                if drama.get('episodes'):
                    ep1_url = drama['episodes'][0]['url']
                    print(f"    Testing video URL from: {ep1_url}")
                    video_urls = await extract_video_url(page, ep1_url)
                    print(f"    Video URLs found: {len(video_urls)}")
                    for vu in video_urls[:5]:
                        print(f"      → {vu[:120]}")
                    drama['sample_video_urls'] = video_urls[:10]
            else:
                print(f"    ❌ Failed: {drama.get('error', '')[:60]}")
        
        # Save
        output = {
            'total_discovered': len(dramas),
            'dramas': drama_list,
        }
        with open('vidrama_discovery.json', 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"\n\n{'='*70}")
        print(f"  Discovery complete: {len(dramas)} dramas found")
        print(f"  Saved: vidrama_discovery.json")
        print(f"{'='*70}")
        
        await browser.close()


if __name__ == '__main__':
    asyncio.run(main())
