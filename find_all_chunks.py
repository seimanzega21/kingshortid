# -*- coding: utf-8 -*-
import requests, re, urllib3, sys
from bs4 import BeautifulSoup
urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

def main():
    watch_url = 'https://vidrama.asia/en/watch/dubbing-apa-ayahku-ternyata-orang-besar--845471/1?provider=shortmax'
    print("Loading watch page to find script chunks...")
    r = requests.get(watch_url, headers=WEB_HDRS, verify=False, timeout=15)
    if not r.ok:
        print("Failed to load watch page:", r.status_code)
        return
        
    soup = BeautifulSoup(r.text, 'html.parser')
    scripts = soup.find_all('script', src=True)
    chunk_urls = []
    for s in scripts:
        src = s['src']
        if '/_next/static/' in src:
            if src.startswith('/'):
                src = 'https://vidrama.asia' + src
            chunk_urls.append(src)
            
    # Also parse next build manifest if present to find more chunks
    build_manifest_match = re.search(r'/_next/static/[^/]+/buildManifest\.js', r.text)
    if build_manifest_match:
        bm_url = 'https://vidrama.asia' + build_manifest_match.group(0)
        chunk_urls.append(bm_url)
        
    print(f"Found {len(chunk_urls)} chunk script URLs.")
    
    # Process each chunk
    for url in chunk_urls:
        print(f"Checking chunk: {url}")
        try:
            res = requests.get(url, headers=WEB_HDRS, verify=False, timeout=10)
            if not res.ok:
                continue
            
            for num in ['7312634', '3927665']:
                match_pat = num + r'\s*:'
                if re.search(match_pat, res.text):
                    print(f"\n>>> FOUND MODULE {num} IN CHUNK: {url} <<<")
                    for match in re.finditer(match_pat, res.text):
                        start = match.start()
                        end = min(len(res.text), match.end() + 2500)
                        print(res.text[start:end])
                        print("=" * 60)
        except Exception as e:
            print("Error checking chunk:", e)

if __name__ == '__main__':
    main()
