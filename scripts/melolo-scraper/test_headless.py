import asyncio
import json
import urllib.parse
from playwright.async_api import async_playwright

drama_slug = "dubbingsopir-taksi-mantan-dewa-balap--846959"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36'
        )
        
        jwt_token = "eyJhbGciOiJFUzI1NiIsImtpZCI6ImY0NTAxYzU1LTY5ZmMtNDczNy05NzFkLTU1OTVjZmRmZDAwNSIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL2drY25ibmxmcWRsb3RuamFpenh4LnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI2ZjNlNWMxNS1hMjFjLTRkMTAtYjg2Yy1lODgxNzBlN2I3MmQiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzc3MTkzMzg2LCJpYXQiOjE3NzcxODk3ODYsImVtYWlsIjoic2VpbWFuemVnYTIxQGdtYWlsLmNvbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZ29vZ2xlIiwicHJvdmlkZXJzIjpbImdvb2dsZSIsImVtYWlsIl19LCJ1c2VyX21ldGFkYXRhIjp7ImF2YXRhcl91cmwiOiJodHRwczovL2xoMy5nb29nbGV1c2VyY29udGVudC5jb20vYS9BQ2c4b2NMT2MwbkFudS01bTcxbmNqRjQ0cDJ0dWJ5cUVjRktVTVg5T25pZW1tX1p3TEdJTVJtdz1zOTYtYyIsImVtYWlsIjoic2VpbWFuemVnYTIxQGdtYWlsLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJmdWxsX25hbWwiOiJzZWltYW4gemVnYSIsImlzcyI6Imh0dHBzOi8vYWNjb3VudHMuZ29vZ2xlLmNvbSIsIm5hbWUiOiJzZWltYW4gemVnYSIsInBpY3R1cmUiOiJodHRwczovL2xoMy5nb29nbGV1c2VyY29udGVudC5jb20vYS9BQ2c4b2NMT2MwbkFudS01bTcxbmNqRjQ0cDJ0dWJ5cUVjRktVTVg5T25pZW1tX1p3TEdJTVJtdz1zOTYtYyIsInByb3ZpZGVyX2lkIjoiMTExODcyOTEzNTI0NDY1MTU0Njg3Iiwic3ViIjoiMTExODcyOTEzNTI0NDY1MTU0Njg3In0sInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiYWFsIjoiYWFsMSIsImFtciI6W3sibWV0aG9kIjoib2F1dGgiLCJ0aW1lc3RhbXAiOjE3NzcxODk3ODZ9XSwic2Vzc2lvbl9pZCI6ImE4YWRiMmQ5LTM1NDQtNDk5OC04ZmViLWNkNjY1ZDY1YzI0NiIsImlzX2Fub255bW91cyI6ZmFsc2V9.jO_nQ5DCLqRkEclv_8D1U631lCq8TjC3zS39nN8E4jJntYp66aYf4XQzZt8yS7iQ9W7u0Jp5pM8JbJ_bQjL0Bw"
        
        page = await context.new_page()
        await page.goto("https://vidrama.asia")
        await page.evaluate(f'''() => {{
            localStorage.setItem('sb-gkcnbnlfqdlotnjaizxx-auth-token', JSON.stringify({{
                "access_token": "{jwt_token}",
                "token_type": "bearer",
                "expires_in": 3600,
                "expires_at": 1777193386,
                "refresh_token": "dummy",
                "user": {{
                    "id": "6f3e5c15-a21c-4d10-b86c-e88170e7b72d",
                    "role": "authenticated"
                }}
            }}));
        }}''')

        found_m3u8 = None
        
        async def handle_request(request):
            if request.method == "POST":
                print(f"[POST] {request.url}")
                print(f"  Headers: {request.headers}")
                print(f"  Data: {request.post_data}")

        async def handle_response(response):
            nonlocal found_m3u8
            req = response.request
            if 'm3u8' in req.url or 'akamai' in req.url:
                print(f"[{req.method}] {req.url} -> {response.status}")
                if 'm3u8' in req.url and 'proxy' not in req.url:
                    found_m3u8 = req.url
            if req.method == "POST":
                print(f"[POST RES] {req.url} -> {response.status}")
                try:
                    text = await response.text()
                    print(f"  Body: {text[:200]}")
                except Exception:
                    print("  Could not read body")

        page.on("request", handle_request)
        page.on("response", handle_response)
        
        print("Navigating to episode 11...")
        try:
            await page.goto(f"https://vidrama.asia/watch/{drama_slug}/11?provider=shortmax", wait_until="networkidle", timeout=30000)
        except Exception as e:
            print(f"Timeout: {e}")
            
        for i in range(10):
            if found_m3u8:
                print(f"SUCCESS! Found M3U8: {found_m3u8}")
                break
            await asyncio.sleep(1)
                
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
