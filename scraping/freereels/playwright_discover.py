"""
Playwright-based discovery of Dubbed Drama IDs from DramaWave.
Uses headless browser to navigate SPA and extract series URLs.
"""
import asyncio, json, re, sys, time, base64, hashlib, os
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

OUTPUT = 'dubbed_series_ids.json'

# Load existing
existing = {}
if Path(OUTPUT).exists():
    with open(OUTPUT, encoding='utf-8') as f:
        existing = json.load(f)
print(f'Existing dubbed IDs: {len(existing)}')

async def collect_ids():
    from playwright.async_api import async_playwright
    
    all_ids = set(existing.keys())
    
    async with async_playwright() as pw:
        br = await pw.chromium.launch(headless=True)
        ctx = await br.new_context(
            viewport={'width': 390, 'height': 844},
            user_agent='Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36',
            locale='id-ID',
        )
        page = await ctx.new_page()
        
        async def extract_ids():
            """Extract all series IDs from current page."""
            try:
                ids = await page.evaluate('''() => {
                    const links = [...document.querySelectorAll("a[href*='/series/']")];
                    const ids = links.map(a => {
                        const m = a.href.match(/\\/series\\/([A-Za-z0-9]{8,12})/);
                        return m ? m[1] : null;
                    }).filter(Boolean);
                    return [...new Set(ids)];
                }''')
                return ids or []
            except:
                # Fallback: get page URL patterns from HTML
                content = await page.content()
                return re.findall(r'/series/([A-Za-z0-9]{8,12})', content)
        
        pages_to_visit = [
            'https://m.mydramawave.com/',
            'https://m.mydramawave.com/free-app/',
        ]
        
        for url in pages_to_visit:
            print(f'\nNavigating to {url}...')
            try:
                await page.goto(url, wait_until='networkidle', timeout=30000)
                await asyncio.sleep(5)
                
                # Scroll multiple times to load more content
                for scroll_n in range(15):
                    await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                    await asyncio.sleep(2)
                    ids = await extract_ids()
                    new_ids = set(ids) - all_ids
                    if new_ids:
                        all_ids.update(new_ids)
                        print(f'  Scroll {scroll_n+1}: +{len(new_ids)} new IDs (total: {len(all_ids)})')
                
                # Try clicking category tabs if available
                try:
                    tabs = await page.query_selector_all('[class*="tab"], [class*="category"], nav a')
                    for tab in tabs[:10]:
                        text = await tab.inner_text()
                        if any(kw in text.lower() for kw in ['dub', 'sulih', 'indo']):
                            print(f'  Clicking tab: {text[:30]}')
                            await tab.click()
                            await asyncio.sleep(3)
                            for scroll in range(10):
                                await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                                await asyncio.sleep(2)
                            ids = await extract_ids()
                            all_ids.update(ids)
                except: pass
                
            except Exception as e:
                print(f'  Error: {e}')
        
        # Try search pages
        for search_term in ['sulih suara', 'dubbing', 'sulih']:
            encoded = search_term.replace(' ', '+')
            search_urls = [
                f'https://m.mydramawave.com/search?q={encoded}',
                f'https://m.mydramawave.com/free-app/search?keyword={encoded}',
            ]
            for search_url in search_urls:
                print(f'\nSearching: {search_url}')
                try:
                    await page.goto(search_url, wait_until='networkidle', timeout=30000)
                    await asyncio.sleep(5)
                    for scroll in range(10):
                        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                        await asyncio.sleep(2)
                    ids = await extract_ids()
                    new_ids = set(ids) - all_ids
                    if new_ids:
                        all_ids.update(new_ids)
                        print(f'  +{len(new_ids)} new IDs from search (total: {len(all_ids)})')
                except Exception as e:
                    print(f'  Error: {e}')
        
        await br.close()
    
    return list(all_ids)

# Run
all_ids = asyncio.run(collect_ids())
print(f'\n\nTotal IDs found: {len(all_ids)}')
print(f'New IDs (not yet validated): {len(set(all_ids) - set(existing.keys()))}')

# Save raw IDs list for validation
with open('raw_series_ids.txt', 'w') as f:
    for sid in all_ids:
        f.write(sid + '\n')
print(f'Saved raw IDs → raw_series_ids.txt')
print('\nNext: run discover_dramas.py with --input raw_series_ids.txt to validate')
