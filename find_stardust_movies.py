# -*- coding: utf-8 -*-
import asyncio
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')

async def main():
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            locale='id-ID',
            extra_http_headers={
                'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
            }
        )
        
        # Add all possible language cookies
        await ctx.add_cookies([
            {'name': 'global_ui_lang', 'value': 'id', 'domain': 'vidrama.asia', 'path': '/'},
            {'name': 'NEXT_LOCALE', 'value': 'id', 'domain': 'vidrama.asia', 'path': '/'},
            {'name': 'next-locale', 'value': 'id', 'domain': 'vidrama.asia', 'path': '/'},
            {'name': 'lang', 'value': 'id', 'domain': 'vidrama.asia', 'path': '/'},
        ])
        
        page = await ctx.new_page()
        
        # Navigate directly to the id locale page if supported, or the main page
        url = 'https://vidrama.asia/provider/stardusttv?lang=id'
        print(f"Loading: {url} with cookies...")
        
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            print("DOM content loaded, waiting 5s for client-side hydration...")
            await asyncio.sleep(5)
            
            # Print current URL
            print(f"Current URL: {page.url}")
            
            # Extract links and titles of movies
            movies = await page.evaluate("""
                () => {
                    const links = Array.from(document.querySelectorAll('a[href*="/movie/"]'));
                    return links.map(l => {
                        const titleText = l.innerText ? l.innerText.trim() : '';
                        const imgAlt = l.querySelector('img') ? l.querySelector('img').getAttribute('alt') : '';
                        const h4Text = l.querySelector('h4') ? l.querySelector('h4').innerText.trim() : '';
                        return {
                            href: l.getAttribute('href'),
                            title: titleText || imgAlt || h4Text
                        };
                    });
                }
            """)
            
            # De-duplicate
            seen = set()
            unique_movies = []
            for m in movies:
                href = m['href']
                if href and href not in seen:
                    seen.add(href)
                    title = m['title'].split('\n')[0].strip() if m['title'] else 'Unknown'
                    unique_movies.append({
                        'href': href,
                        'title': title
                    })
                    
            print(f"\nFound {len(unique_movies)} unique movies:")
            for i, m in enumerate(unique_movies):
                print(f"  {i+1}: {m['title']} -> {m['href']}")
                
            # Write to a JSON file
            with open('stardust_movies_global_lang.json', 'w', encoding='utf-8') as f:
                json.dump(unique_movies, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Error: {e}")
            
        await browser.close()

asyncio.run(main())
