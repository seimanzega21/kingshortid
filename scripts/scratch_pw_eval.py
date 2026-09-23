import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # Let's inspect window.__next_f or find all server references in window
        await page.goto("https://vidrama.asia/en/watch/pahlawan-kecil-yang-misterius--865915/1?provider=shortmax&lang=id", wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)

        # Let's evaluate scripts in page to see webpack or turbopack modules
        res = await page.evaluate("""() => {
            // Find any global objects or scripts
            let scripts = Array.from(document.querySelectorAll('script')).map(s => s.src).filter(Boolean);
            return {
                scripts: scripts,
                hasTurbopack: !!window.__turbopack_load__,
                keys: Object.keys(window).filter(k => k.includes('next') || k.includes('turbo'))
            };
        }""")
        print("Page JS info:", res)

        await browser.close()

asyncio.run(run())
