"""
Capture FreeReels Google Login Auth Token
==========================================
Opens a VISIBLE browser window → you manually login with Google →
script automatically captures auth_key and auth_secret.

Run: python capture_google_token.py
Then login with: dhikarentcar@gmail.com
"""
import asyncio, json, sys, re
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

TOKEN_FILE = Path('fr_vip_token.json')
captured = {}

async def capture():
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        # NON-headless: visible browser so you can login manually
        br = await pw.chromium.launch(
            headless=False,
            args=['--no-sandbox', '--disable-web-security'],
        )
        ctx = await br.new_context(
            viewport={'width': 430, 'height': 900},
            user_agent='Mozilla/5.0 (Linux; Android 12; Pixel 6)',
            locale='id-ID',
        )
        page = await ctx.new_page()

        # Intercept API responses
        async def on_response(resp):
            if 'apiv2.free-reels.com' not in resp.url:
                return
            try:
                body = await resp.body()
                text = body.decode('utf-8', errors='replace')
                data = json.loads(text)
                inner = data.get('data', {})
                ak  = inner.get('auth_key', '')
                ase = inner.get('auth_secret', '')
                if ak and ase:
                    captured['auth_key']    = ak
                    captured['auth_secret'] = ase
                    captured['user_id']     = inner.get('user_id', '')
                    captured['nickname']    = inner.get('nickname', inner.get('name', ''))
                    print(f'\n✓ AUTH CAPTURED!')
                    print(f'  auth_key:    {ak[:20]}...')
                    print(f'  auth_secret: {ase[:20]}...')
                    print(f'  user_id:     {inner.get("user_id")}')
                    print(f'  nickname:    {inner.get("nickname", "")}')
                    TOKEN_FILE.write_text(json.dumps(captured, indent=2))
                    print(f'\nSaved → {TOKEN_FILE}')
                    print('You can close the browser window now.')
            except:
                pass

        page.on('response', on_response)

        print('Opening FreeReels... Please wait.')
        await page.goto('https://free-reels.com/', wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(3)

        # Try to click Login button
        try:
            for sel in ['[class*="login"]', 'button:has-text("Login")', 'a:has-text("Login")',
                       '[class*="sign"]', 'button:has-text("Sign")', 'text=Login']:
                btn = await page.query_selector(sel)
                if btn:
                    await btn.click()
                    print('Clicked Login button')
                    break
        except:
            pass

        print('\n' + '='*50)
        print('INSTRUCTIONS:')
        print('1. Click "Login with Google" in the browser')
        print('2. Select account: dhikarentcar@gmail.com')
        print('3. Wait for login to complete')
        print('4. Script will auto-capture the token')
        print('='*50)
        print('\nWaiting for Google login... (90 seconds)')

        # Wait up to 90 seconds for token to be captured
        for i in range(90):
            if captured.get('auth_key'):
                break
            await asyncio.sleep(1)
            if i % 10 == 9:
                print(f'  Waiting... {90-i-1}s remaining')

        if not captured.get('auth_key'):
            print('\n[TIMEOUT] Token not captured. Try again or check network tab.')
        
        await asyncio.sleep(5)
        await br.close()

    return captured

result = asyncio.run(capture())

if result.get('auth_key'):
    print('\n\nTOKEN READY! Now update freereels_master.py:')
    print(f'\nAUTH_KEY    = "{result["auth_key"]}"')
    print(f'AUTH_SECRET = "{result["auth_secret"]}"')
else:
    print('\nNo token captured.')
