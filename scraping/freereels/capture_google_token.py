"""
Capture FreeReels Google Login Token
=====================================
Opens a VISIBLE Chrome browser. Login dengan Google.
Script auto-capture auth_key + auth_secret dari API response.

Run: python capture_google_token.py
Login: dhikarentcar@gmail.com
"""
import asyncio, json, sys, time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

TOKEN_FILE = Path('fr_vip_token.json')
captured = {}

async def capture():
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        br = await pw.chromium.launch(
            headless=False,
            args=['--start-maximized', '--no-sandbox'],
        )
        ctx = await br.new_context(
            viewport=None,  # maximize window
            user_agent='Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0 Mobile Safari/537.36',
            locale='id-ID',
        )
        page = await ctx.new_page()

        # Intercept ALL API responses from FreeReels
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
                if ak and ase and len(ak) > 8:
                    captured['auth_key']    = ak
                    captured['auth_secret'] = ase
                    captured['user_id']     = str(inner.get('user_id', ''))
                    captured['nickname']    = str(inner.get('nickname', inner.get('name', '')))
                    TOKEN_FILE.write_text(json.dumps(captured, indent=2, ensure_ascii=False), encoding='utf-8')
                    print(f'\n{"="*50}')
                    print(f'TOKEN BERHASIL DICAPTURE!')
                    print(f'  auth_key:    {ak[:20]}...')
                    print(f'  auth_secret: {ase[:20]}...')
                    print(f'  user_id:     {inner.get("user_id")}')
                    print(f'  nickname:    {inner.get("nickname","")}')
                    print(f'Saved → {TOKEN_FILE}')
                    print(f'{"="*50}')
                    print('\nBisa tutup browser sekarang!')
            except Exception as e:
                pass

        page.on('response', on_response)

        print('Membuka FreeReels...')
        await page.goto('https://free-reels.com/', timeout=30000)
        await asyncio.sleep(3)

        print('\n' + '='*50)
        print('BROWSER SUDAH TERBUKA!')
        print()
        print('Langkah:')
        print('1. Cari ikon user / tombol "Login" di pojok kanan atas')
        print('2. Klik "Continue with Google"')
        print('3. Pilih: dhikarentcar@gmail.com')
        print('4. Setelah login selesai, token otomatis tersimpan')
        print()
        print('Script menunggu 3 menit ...')
        print('='*50)

        # Wait 3 minutes (180 seconds)
        for i in range(180):
            if captured.get('auth_key'):
                print('\n>>> TOKEN CAPTURED! Bisa tutup browser <<<')
                await asyncio.sleep(5)
                break
            await asyncio.sleep(1)
            if i % 20 == 19:
                remaining = 180 - i - 1
                print(f'  Menunggu login... {remaining}s tersisa')

        if not captured.get('auth_key'):
            print('\n[TIMEOUT] Token tidak ter-capture setelah 3 menit.')
            print()
            print('Coba alternatif manual:')
            print('1. Buka Chrome biasa → https://free-reels.com')
            print('2. Login dengan Google')
            print('3. Tekan F12 → Network → ketik "apiv2" di filter')
            print('4. Refresh halaman → cari request yang ada auth_key di response')
            print('5. Copy auth_key dan auth_secret ke fr_vip_token.json')

        await asyncio.sleep(3)
        await br.close()

    return captured

result = asyncio.run(capture())

if result.get('auth_key'):
    print('\n\nSiap! Jalankan pipeline sekarang:')
    print('python freereels_master.py --download --limit 259')
