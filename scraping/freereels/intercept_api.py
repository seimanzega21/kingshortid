"""
Playwright intercept on free-reels.com to capture catalog API calls.
"""
import asyncio, json, base64, os, sys, time, hashlib
from playwright.async_api import async_playwright
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
AES_KEY = b'2r36789f45q01ae5'

def dec(t):
    try:
        r = base64.b64decode(t); iv, ct = r[:16], r[16:]
        c = Cipher(algorithms.AES(AES_KEY[:16]), modes.CBC(iv), backend=default_backend())
        p = c.decryptor().update(ct) + c.decryptor().finalize()
        return json.loads(p[:-p[-1]].decode())
    except:
        try: return json.loads(t)
        except: return None

requests_log = []
responses_log = []

async def main():
    async with async_playwright() as pw:
        br = await pw.chromium.launch(headless=False)  # Visible browser
        ctx = await br.new_context(viewport={'width': 390, 'height': 844})
        page = await ctx.new_page()

        async def on_req(req):
            url = req.url
            if any(d in url for d in ['api.mydramawave', 'apiv2.free-reels', 'api.free-reels']):
                body = req.post_data or ''
                dec_body = dec(body) if body else None
                entry = {'method': req.method, 'url': url, 'body': dec_body or body[:200],
                         'hdrs': {k: v for k,v in req.headers.items() if k in [
                             'authorization', 'app-name', 'device', 'country', 'language']}}
                requests_log.append(entry)
                path = url.split('.com')[-1]
                print(f'REQ {req.method} {path[:80]}')
                if dec_body:
                    print(f'  body: {json.dumps(dec_body)[:150]}')

        async def on_resp(resp):
            url = resp.url
            if any(d in url for d in ['api.mydramawave', 'apiv2.free-reels', 'api.free-reels']):
                try:
                    text = await resp.text()
                    d = dec(text)
                    entry = {'url': url, 'status': resp.status, 'data': d}
                    responses_log.append(entry)
                    path = url.split('.com')[-1]
                    code = d.get('code', '?') if d else '?'
                    print(f'RES {resp.status} {path[:80]} -> code={code}')
                    if d and d.get('code') in [200, 0]:
                        data = d.get('data', {})
                        if isinstance(data, dict):
                            items = data.get('list', data.get('items', []))
                            if items:
                                print(f'  first_keys: {list(items[0].keys()) if isinstance(items[0], dict) else type(items[0]).__name__}')
                except: pass

        page.on('request', on_req)
        page.on('response', on_resp)

        # Navigate to free-reels.com
        print('=== Navigating to free-reels.com ===')
        await page.goto('https://www.free-reels.com', wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(8)
        print(f'Requests: {len(requests_log)}, Responses: {len(responses_log)}')

        # Try mydramawave if free-reels doesn't work
        if len(requests_log) == 0:
            print('\n=== Trying m.mydramawave.com ===')
            await page.goto('https://m.mydramawave.com/free-app/', wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(10)
            print(f'Requests: {len(requests_log)}, Responses: {len(responses_log)}')

        # Try to click any "Dub" or "Dubbing" tab
        await asyncio.sleep(3)
        for text in ['Dub', 'Dubbed', 'Dubbing', 'Indonesia', 'Dub\n']:
            try:
                el = page.get_by_text(text, exact=True)
                if await el.count() > 0:
                    await el.first.click()
                    print(f'Clicked: {text}')
                    await asyncio.sleep(5)
                    break
            except: pass

        # Save
        all_data = {'requests': requests_log, 'responses': responses_log}
        with open('playwright_capture.json', 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        print(f'\nSaved. Requests: {len(requests_log)}, Responses: {len(responses_log)}')

        await asyncio.sleep(2)
        await br.close()

asyncio.run(main())
