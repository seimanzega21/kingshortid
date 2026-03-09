"""
Use Playwright to intercept FreeReels web network calls.
Captures actual API requests to apiv2.free-reels.com including
the correct tab feed body format and series IDs from tab 514.
"""
import asyncio, json, sys, time, re
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

captured = []
series_ids = set()

async def intercept():
    from playwright.async_api import async_playwright
    
    async with async_playwright() as pw:
        br = await pw.chromium.launch(headless=True)
        ctx = await br.new_context(
            viewport={'width': 390, 'height': 844},
            user_agent='Mozilla/5.0 (Linux; Android 12)',
            locale='id-ID',
        )
        
        # Intercept all API calls
        async def on_request(req):
            if 'apiv2.free-reels.com' in req.url or 'free-reels.com/frv2' in req.url:
                try:
                    body_bytes = req.post_data
                    info = {'url': req.url, 'method': req.method, 'body': body_bytes, 'headers': dict(req.headers)}
                    captured.append(info)
                    print(f'  → {req.method} {req.url}')
                    if body_bytes:
                        print(f'    body: {body_bytes[:100]}')
                except: pass
        
        async def on_response(resp):
            if 'apiv2.free-reels.com' in resp.url:
                try:
                    body = await resp.body()
                    body_str = body.decode('utf-8', errors='replace')[:200]
                    # Find series IDs in response  
                    ids = re.findall(r'"id"\s*:\s*"([A-Za-z0-9]{8,12})"', body_str)
                    if ids:
                        series_ids.update(ids)
                        print(f'    ← response IDs: {ids[:3]}')
                    # Also numeric
                    num_ids = re.findall(r'"series_id"\s*:\s*(\d{4,8})', body_str)
                    if num_ids:
                        series_ids.update(num_ids)
                        print(f'    ← numeric series_ids: {num_ids[:3]}')
                except: pass
        
        page = await ctx.new_page()
        page.on('request', on_request)
        page.on('response', on_response)
        
        print('Navigating to FreeReels...')
        await page.goto('https://free-reels.com/', wait_until='networkidle', timeout=30000)
        await asyncio.sleep(8)
        print(f'Captured {len(captured)} API calls so far')
        
        # Try to find and click Dubbed tab
        print('\nLooking for Dubbed tab...')
        try:
            tabs = await page.query_selector_all('[class*="tab"], [class*="category"], [class*="nav"] a, [class*="menu"] a')
            for tab in tabs:
                text = await tab.inner_text()
                print(f'  Tab: {text[:30]}')
                if any(kw in text.lower() for kw in ['dub', 'sulih', 'indo', '514']):
                    print(f'  → Clicking: {text[:30]}')
                    await tab.click()
                    await asyncio.sleep(5)
                    
                    # Scroll to load more
                    for _ in range(5):
                        await page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
                        await asyncio.sleep(2)
        except Exception as e:
            print(f'Tab click error: {e}')
        
        # Extract series IDs from current page links
        try:
            ids_from_links = await page.evaluate('''() => {
                const links = [...document.querySelectorAll('a[href]')];
                const ids = new Set();
                links.forEach(a => {
                    const m = a.href.match(/\/(series|drama|watch)\/([A-Za-z0-9]{4,15})/);
                    if (m) ids.add(m[2]);
                    const n = a.href.match(/\/(series|drama|watch)\/(\d{4,10})/);
                    if (n) ids.add(n[2]);
                });
                return [...ids];
            }''')
            if ids_from_links:
                print(f'\nSeries IDs from page links: {ids_from_links[:10]}')
                series_ids.update(ids_from_links)
        except: pass
        
        # Try navigating directly to known URL patterns
        for path_try in ['/dubbed', '/dub', '/id', '/indonesia', '/category/14', '/series']:
            try:
                await page.goto(f'https://free-reels.com{path_try}', 
                               wait_until='networkidle', timeout=15000)
                await asyncio.sleep(4)
                ids = await page.evaluate('''() => {
                    const links = [...document.querySelectorAll('a[href]')];
                    const ids = [];
                    links.forEach(a => {
                        const m = a.href.match(/\/(series|drama)\/([A-Za-z0-9]{4,15})/);
                        if (m) ids.push({ url: a.href, id: m[2] });
                    });
                    return ids.slice(0, 20);
                }''')
                if ids:
                    print(f'\n{path_try}: Found IDs: {[i["id"] for i in ids[:5]]}')
                    series_ids.update(i['id'] for i in ids)
            except: pass
        
        await br.close()
    
    return list(series_ids)

print('=== FreeReels Network Intercept ===')
ids = asyncio.run(intercept())
print(f'\nTotal captured API calls: {len(captured)}')
print(f'Total series IDs found: {len(ids)}')

# Save results
with open('fr_captured.json', 'w', encoding='utf-8') as f:
    json.dump({'calls': captured, 'series_ids': ids}, f, ensure_ascii=False, indent=2)

print('\nAll captured API calls:')
for c in captured:
    print(f'  {c["method"]} {c["url"][:80]}')

print(f'\nSeries IDs: {ids[:20]}')
print('\nSaved → fr_captured.json')
