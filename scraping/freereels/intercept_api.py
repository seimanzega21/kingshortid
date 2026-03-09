"""
Playwright: intercept DramaWave episode page API requests to:
1. Get a valid series_id
2. Capture drama/view response with episode_list + external_audio_h264_m3u8 fields
"""
import asyncio, json, base64, os, sys
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

captured = []

async def main():
    async with async_playwright() as pw:
        br = await pw.chromium.launch(headless=True)
        ctx = await br.new_context(
            viewport={'width': 390, 'height': 844},
            user_agent='Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36',
        )
        page = await ctx.new_page()

        async def intercept(route, req):
            url = req.url
            is_api = any(d in url for d in [
                'api.mydramawave.com', 'apiv2.free-reels.com', 'api.free-reels.com'
            ])
            if is_api:
                body = req.post_data or ''
                dec_body = dec(body) if body else {}
                entry = {
                    'method': req.method,
                    'url': url,
                    'body': dec_body if dec_body else body[:100],
                    'hdrs': {k: v for k, v in req.headers.items()
                             if k in ['authorization', 'app-name', 'country', 'language']},
                }
                resp = await route.fetch()
                text = await resp.text()
                dec_resp = dec(text)
                entry['resp_code'] = dec_resp.get('code') if dec_resp else None
                entry['resp_data'] = dec_resp
                captured.append(entry)
                path = url.split('.com')[-1][:60]
                code = entry['resp_code']
                print(f'{req.method} {path} -> code={code}')
                if dec_resp and dec_resp.get('code') in [200, 0]:
                    data = dec_resp.get('data', {})
                    if isinstance(data, dict):
                        ep_list = data.get('episode_list', data.get('episodes', []))
                        if ep_list:
                            ep = ep_list[0] if ep_list else {}
                            print(f'  ep_list[0] audio keys: {[k for k in ep.keys() if "audio" in k.lower() or "m3u8" in k.lower() or "url" in k.lower()]}')
                await route.fulfill(response=resp)
            else:
                await route.continue_()

        await page.route('**/*', intercept)

        print('=== Loading DramaWave (country=ID) ===')
        page.set_extra_http_headers({'country': 'ID', 'language': 'id'})
        try:
            await page.goto('https://m.mydramawave.com/free-app/', timeout=30000)
            await asyncio.sleep(15)
            print(f'Captured {len(captured)} API calls')
        except Exception as e:
            print(f'Error: {e}')

        # Save
        with open('playwright_api.json', 'w', encoding='utf-8') as f:
            json.dump(captured, f, ensure_ascii=False, indent=2, default=str)
        print(f'Saved {len(captured)} events')
        
        # print all unique endpoints found
        print('\nAPIs found:')
        for ev in captured:
            path = ev['url'].split('.com')[-1][:60]
            print(f'  {ev["method"]} {path} code={ev.get("resp_code")}')
            if isinstance(ev.get('body'), dict):
                print(f'    body={json.dumps(ev["body"])[:100]}')

        await br.close()

asyncio.run(main())
