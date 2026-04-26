import asyncio
import urllib.parse
from pathlib import Path
from playwright.async_api import async_playwright
import os

TITLES = [
    "Tuan Gelap",
    "[Dubbing]Cinta Kadaluarsa",
    "[Dijuluki]Ada Ayah Mendukungmu",
    "[Dubbing]Raja Naga",
    "[Dijuluki]Kebangkitan Hari Ini",
    "Penguasa Tanpa Lawan",
    "Penakluk Hati",
    "[Dubbing] Bos Muda Lelah Jadi Pewaris Hanya Ingin Bekerja Keras",
    "[Dubbing]Dulu Menyelamatkan Kini Diselamatkan",
    "[Dubbing]Dunia Lebih Indah Dari Surga",
    "Rupanya Satpam itu Kaya Raya"
]

PROFILE_DIR = Path("d:/kingshortid/scripts/melolo-scraper/vidrama_profile")

async def get_slug_from_title(title: str, context):
    page = await context.new_page()
    await page.goto(f"https://vidrama.asia/search?q={urllib.parse.quote(title)}", wait_until="networkidle")
    try:
        # Wait for links to appear
        await page.wait_for_selector('a[href^="/movie/"]', timeout=10000)
        href = await page.locator('a[href^="/movie/"]').first.get_attribute('href')
        # href is like /movie/tuan-gelap--12345?provider=shortmax
        slug = href.split('/movie/')[1].split('?')[0]
        
        provider = "shortmax"
        if "?provider=" in href:
            provider = href.split("?provider=")[1].split("&")[0]
        elif "provider=" in href:
            provider = href.split("provider=")[1].split("&")[0]
            
        await page.close()
        return slug, provider
    except Exception as e:
        print(f"[-] Failed to find slug for {title}: {e}")
        await page.close()
        return None, None

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        )
        
        slugs_and_providers = []
        for t in list(dict.fromkeys(TITLES)): # Remove duplicates but keep order
            print(f"[*] Searching for: {t}")
            slug, provider = await get_slug_from_title(t, context)
            if slug:
                print(f"    -> Found slug: {slug} (Provider: {provider})")
                slugs_and_providers.append((slug, provider))
                
        await context.close()
        
        # Now run the headless scraper for each slug
        for slug, provider in slugs_and_providers:
            print(f"\n=======================================================")
            print(f"[*] RUNNING SCRAPER FOR: {slug}")
            print(f"=======================================================")
            os.system(f"python d:/kingshortid/scripts/melolo-scraper/vidrama_shortmax_headless.py {slug} {provider}")

if __name__ == "__main__":
    asyncio.run(main())
