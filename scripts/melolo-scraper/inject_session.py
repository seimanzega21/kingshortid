import asyncio
import json
import urllib.parse
from pathlib import Path
from playwright.async_api import async_playwright

PROFILE_DIR = Path("d:/kingshortid/scripts/melolo-scraper/vidrama_profile")

RAW_COOKIE = """_fbp=fb.1.1770653154777.876935444165455244; _tt_enable_cookie=1; _ttp=01KH1JE0K4H648BY6E3FQ6EXRZ_.tt.1; _ga=GA1.1.1826262121.1771037718; HstCfa5004644=1772873251576; c_ref_5004644=https%3A%2F%2Fwww.google.com%2F; __dtsu=4C301774685394D291D3AB624E4AA57E; _pubcid=8a5abbf9-164b-422f-b349-0e1ba702ea69; _cc_id=a4a99f9a552125d19ea447bfafb9c63b; HstCmu5004644=1776164034743; HstCnv5004644=27; panoramaId_expiry=1777287889182; HstCns5004644=31; cf_clearance=xYz4IfsVuHT_ve0vl00klXI5KMgicgbdxtOFBaqYQm8-1777202365-1.2.1.1-8qhICsDULuwd3_twsMF5RdD.a9wVwxgq2Hj4.KDJVXhf_kV6i.Phkh6k1zRUgwbXXOsCggcARXWoplzRMgBRGY2GE93EN03TVX8DBeSH0hxpKj.0Jtsea6rgvb24cfHPCPLNVvDCRCcSDWMnbG9jzyPQbJ7uBxI1TH6_6G76sPJi9JA.yLoKjo71KjXA6AK5ISvf.kxE_xDal_5qyE5.eDe4wn8JHcc7cpH4sbvcnsE9BkDi6P6Wb2bUCsIsi1bQexCthfBQg5JlaUgMpkUX9W3W7bJUDGpV1aFB6q8hwr7xfVidRwxUMpvu2jLsc1DeOtaqwxJsQ_mIuyIbPqv1Og; _ga_HCQQPKGEVH=GS2.1.s1777198038$o63$g1$t1777202365$j28$l0$h0; ttcsid=1777198035982::TQUkO9aH-bW4jAVN3BeC.74.1777202366345.0::1.4328775.4330083::4307804.99.79.518::4309585.297.0; ttcsid_D5SNQPRC77UDQTF8A5EG=1777198037487::-RtfUorGP5qejknZdqYu.68.1777202366345.1; HstCla5004644=1777202483876; HstPn5004644=6; HstPt5004644=68"""

# The fresh token string
TOKEN_STR = '{"access_token":"eyJhbGciOiJFUzI1NiIsImtpZCI6ImY0NTAxYzU1LTY5ZmMtNDczNy05NzFkLTU1OTVjZmRmZDAwNSIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL2drY25ibmxmcWRsb3RuamFpenh4LnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI2ZjNlNWMxNS1hMjFjLTRkMTAtYjg2Yy1lODgxNzBlN2I3MmQiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzc3MjA1MTAxLCJpYXQiOjE3NzcyMDE1MDEsImVtYWlsIjoic2VpbWFuemVnYTIxQGdtYWlsLmNvbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZ29vZ2xlIiwicHJvdmlkZXJzIjpbImdvb2dsZSIsImVtYWlsIl19LCJ1c2VyX21ldGFkYXRhIjp7ImF2YXRhcl91cmwiOiJodHRwczovL2xoMy5nb29nbGV1c2VyY29udGVudC5jb20vYS9BQ2c4b2NLTHVLNzltN2xuOWdBcXJRVEhNVFFDZTFRR3B3Vy10dHh2RW1lNWUzSTF2OHBubGpvPXM5Ni1jIiwiZW1haWwiOiJzZWltYW56ZWdhMjFAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZ1bGxfbmFtZSI6InNlaW1hbiB6ZWdhIiwiaXNzIjoiaHR0cHM6Ly9hY2NvdW50cy5nb29nbGUuY29tIiwibmFtZSI6InNlaW1hbiB6ZWdhIiwicGhvbmVfdmVyaWZpZWQiOmZhbHNlLCJwaWN0dXJlIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EvQUNnOG9jS0x1Szc5bTdsbjlnQXFyUVRITVRRQ2UxUUdwd1ctdHR4dkVtZTVlM0kxdjhwbmxqbz1zOTYtYyIsInByb3ZpZGVyX2lkIjoiMTA3NjA4MDAzMDIzNjk0ODg5MzE3Iiwic3ViIjoiMTA3NjA4MDAzMDIzNjk0ODg5MzE3In0sInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiYWFsIjoiYWFsMSIsImFtciI6W3sibWV0aG9kIjoicGFzc3dvcmQiLCJ0aW1lc3RhbXAiOjE3NzcyMDE1MDF9XSwic2Vzc2lvbl9pZCI6IjA2YzEyZGE2LTgxNzktNDFlOS1hYTVjLTZkZjAyM2IzMDg3ZiIsImlzX2Fub255bW91cyI6ZmFsc2V9.NEQxC2GgYRF12ngTHaSrarxeKsvXImmkMWOnIP1pZ72e7rmB4QxIF6TkK5tI8TcWkNSlV2gcHC3e2IAuPvjqsA","token_type":"bearer","expires_in":3600,"expires_at":1777205101,"refresh_token":"4pwgragntiub","user":{"id":"6f3e5c15-a21c-4d10-b86c-e88170e7b72d","aud":"authenticated","role":"authenticated","email":"seimanzega21@gmail.com","email_confirmed_at":"2026-02-09T16:14:28.718318Z","phone":"","confirmation_sent_at":"2026-02-09T16:10:50.532782Z","confirmed_at":"2026-02-09T16:14:28.718318Z","last_sign_in_at":"2026-04-26T11:05:01.121632633Z","app_metadata":{"provider":"google","providers":["google","email"]},"user_metadata":{"avatar_url":"https://lh3.googleusercontent.com/a/ACg8ocKLuK79m7ln9gAqrQTHMTQCe1QGpwW-ttxvEme5e3I1v8pnljo=s96-c","email":"seimanzega21@gmail.com","email_verified":true,"full_name":"seiman zega","iss":"https://accounts.google.com","name":"seiman zega","phone_verified":false,"picture":"https://lh3.googleusercontent.com/a/ACg8ocKLuK79m7ln9gAqrQTHMTQCe1QGpwW-ttxvEme5e3I1v8pnljo=s96-c","provider_id":"107608003023694889317","sub":"107608003023694889317"},"identities":[{"identity_id":"3f6ca687-3932-4930-88ff-08acca1b681d","id":"107608003023694889317","user_id":"6f3e5c15-a21c-4d10-b86c-e88170e7b72d","identity_data":{"avatar_url":"https://lh3.googleusercontent.com/a/ACg8ocKLuK79m7ln9gAqrQTHMTQCe1QGpwW-ttxvEme5e3I1v8pnljo=s96-c","email":"seimanzega21@gmail.com","email_verified":true,"full_name":"seiman zega","iss":"https://accounts.google.com","name":"seiman zega","phone_verified":false,"picture":"https://lh3.googleusercontent.com/a/ACg8ocKLuK79m7ln9gAqrQTHMTQCe1QGpwW-ttxvEme5e3I1v8pnljo=s96-c","provider_id":"107608003023694889317","sub":"107608003023694889317"},"provider":"google","last_sign_in_at":"2026-03-09T01:29:42.8377Z","created_at":"2026-03-09T01:29:42.838274Z","updated_at":"2026-03-09T01:29:42.838274Z","email":"seimanzega21@gmail.com"},{"identity_id":"49be2413-817a-4128-95d4-bee97757fb12","id":"6f3e5c15-a21c-4d10-b86c-e88170e7b72d","user_id":"6f3e5c15-a21c-4d10-b86c-e88170e7b72d","identity_data":{"email":"seimanzega21@gmail.com","email_verified":true,"name":"Seiman Zega","phone_verified":false,"sub":"6f3e5c15-a21c-4d10-b86c-e88170e7b72d"},"provider":"email","last_sign_in_at":"2026-02-09T16:10:50.52732Z","created_at":"2026-02-09T16:10:50.527403Z","updated_at":"2026-02-09T16:10:50.527403Z","email":"seimanzega21@gmail.com"}],"created_at":"2026-02-09T16:10:50.493379Z","updated_at":"2026-04-26T11:05:01.183502Z","is_anonymous":false},"weak_password":null}'

async def main():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            headless=True,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        # Parse raw cookies
        cookies = []
        for chunk in RAW_COOKIE.split(';'):
            chunk = chunk.strip()
            if not chunk: continue
            k, v = chunk.split('=', 1)
            cookies.append({
                "name": k,
                "value": v,
                "domain": "vidrama.asia",
                "path": "/"
            })
            cookies.append({
                "name": k,
                "value": v,
                "domain": ".vidrama.asia",
                "path": "/"
            })
            
        # Add the Supabase cookie as well
        token_data = json.loads(TOKEN_STR)
        cookie_val = urllib.parse.quote(json.dumps([
            token_data['access_token'],
            token_data['refresh_token'], None, None, None
        ]))
        cookies.append({
            "name": "sb-gkcnbnlfqdlotnjaizxx-auth-token",
            "value": cookie_val,
            "domain": "vidrama.asia",
            "path": "/"
        })
        cookies.append({
            "name": "sb-gkcnbnlfqdlotnjaizxx-auth-token",
            "value": cookie_val,
            "domain": ".vidrama.asia",
            "path": "/"
        })

        await context.add_cookies(cookies)
        print("[+] Added cookies to persistent context!")
        
        page = await context.new_page()
        await page.goto("https://vidrama.asia")
        await page.evaluate(f'''() => {{
            localStorage.setItem('sb-gkcnbnlfqdlotnjaizxx-auth-token', `{TOKEN_STR}`);
        }}''')
        print("[+] Injected token to localStorage.")
        
        # Verify
        await page.goto("https://vidrama.asia/movie/cahaya-di-balik-gelap--1987705627844739073?provider=shortmax", wait_until="networkidle")
        title = await page.evaluate("document.querySelector('h1')?.innerText || ''")
        print(f"[!] Target Page Title: {title}")
        
        await asyncio.sleep(2)
        await context.close()

if __name__ == "__main__":
    asyncio.run(main())
