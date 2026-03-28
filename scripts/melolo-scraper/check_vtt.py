import asyncio
import json
from playwright.async_api import async_playwright

AUTH_DATA = {
    "access_token": "eyJhbGciOiJFUzI1NiIsImtpZCI6ImY0NTAxYzU1LTY5ZmMtNDczNy05NzFkLTU1OTVjZmRmZDAwNSIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL2drY25ibmxmcWRsb3RuamFpenh4LnN1cGFiYXNlLmNvL2F1dGgvdjEiLCJzdWIiOiI2ZjNlNWMxNS1hMjFjLTRkMTAtYjg2Yy1lODgxNzBlN2I3MmQiLCJhdWQiOiJhdXRoZW50aWNhdGVkIiwiZXhwIjoxNzc0NjkzMzkxLCJpYXQiOjE3NzQ2ODk3OTEsImVtYWlsIjoic2VpbWFuemVnYTIxQGdtYWlsLmNvbSIsInBob25lIjoiIiwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiZ29vZ2xlIiwicHJvdmlkZXJzIjpbImdvb2dsZSIsImVtYWlsIl19LCJ1c2VyX21ldGFkYXRhIjp7ImF2YXRhcl91cmwiOiJodHRwczovL2xoMy5nb29nbGV1c2VyY29udGVudC5jb20vYS9BQ2c4b2NLTHVLNzltN2xuOWdBcXJRVEhNVFFDZTFRR3B3Vy10dHh2RW1lNWUzSTF2OHBubGpvPXM5Ni1jIiwiZW1haWwiOiJzZWltYW56ZWdhMjFAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZ1bGxfbmFtZSI6InNlaW1hbiB6ZWdhIiwiaXNzIjoiaHR0cHM6Ly9hY2NvdW50cy5nb29nbGUuY29tIiwibmFtZSI6InNlaW1hbiB6ZWdhIiwicGhvbmVfdmVyaWZpZWQiOmZhbHNlLCJwaWN0dXJlIjoiaHR0cHM6Ly9saDMuZ29vZ2xldXNlcmNvbnRlbnQuY29tL2EvQUNnOG9jS0x1Szc5bTdsbjlnQXFyUVRITVRRQ2UxUUdwd1ctdHR4dkVtZTVlM0kxdjhwbmxqbz1zOTYtYyIsInByb3ZpZGVyX2lkIjoiMTA3NjA4MDAzMDIzNjk0ODg5MzE3Iiwic3ViIjoiMTA3NjA4MDAzMDIzNjk0ODg5MzE3In0sInJvbGUiOiJhdXRoZW50aWNhdGVkIiwiYWFsIjoiYWFsMSIsImFtciI6W3sibWV0aG9kIjoicGFzc3dvcmQiLCJ0aW1lc3RhbXAiOjE3NzQ2ODk3OTF9XSwic2Vzc2lvbl9pZCI6ImE0NTM5MWFjLWM4YWItNDI3ZC05OTNkLWFhZDYxMjI0MTJlYyIsImlzX2Fub255bW91cyI6ZmFsc2V9.V3BqHWPqGHVkkE9Sqb4IOJcPO51ZblyWk_oZbfyJgP1y9dh_HUV4Snd_AKkEoeWLELPlEcjpLSIu6OP7Q9K-kw",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": {"id": "6f3e5c15-a21c-4d10-b86c-e88170e7b72d", "email": "seimanzega21@gmail.com"}
}

async def main():
    urls = []
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context()
        page = await ctx.new_page()
        
        async def on_response(response):
            if response.request.resource_type in ["xhr", "fetch"]:
                try: 
                    urls.append(f"[{response.status}] {response.url}")
                except:
                    pass
                
        page.on("response", on_response)
        
        await page.goto("https://vidrama.asia", timeout=30000)
        await page.evaluate(f"""
            localStorage.setItem(
                'sb-gkcnbnlfqdlotnjaizxx-auth-token',
                JSON.stringify({json.dumps(AUTH_DATA)})
            );
            localStorage.setItem('vidrama_subscription_cache', JSON.stringify({{
                "userId": "123", "status": "vip", "tier": "vip", "timestamp": Date.now()
            }}));
        """)
        
        await page.goto("https://vidrama.asia/watch/gejolak-keluarga-konglomerat--2034897075744800770/1?provider=netshort", timeout=60000)
        await page.wait_for_timeout(8000)
        
        for u in urls:
            if "subtitle" in u.lower() or "caption" in u.lower() or "file" in u.lower() or "mp4" not in u.lower():
                print(u)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
