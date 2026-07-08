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
    r = requests.get(watch_url, headers=WEB_HDRS, verify=False, timeout=15)
    soup = BeautifulSoup(r.text, 'html.parser')
    scripts = soup.find_all('script', src=True)
    chunk_urls = []
    for s in scripts:
        src = s['src']
        if '/_next/static/' in src:
            if src.startswith('/'):
                src = 'https://vidrama.asia' + src
            chunk_urls.append(src)
            
    for url in chunk_urls:
        try:
            res = requests.get(url, headers=WEB_HDRS, verify=False, timeout=10)
            if not res.ok:
                continue
            
            # Search for the string "7312634" in the entire chunk
            if "7312634" in res.text:
                print(f"\n>>> FOUND '7312634' IN CHUNK: {url} <<<")
                # Print occurrences with context
                for m in re.finditer(r'7312634', res.text):
                    start = max(0, m.start() - 200)
                    end = min(len(res.text), m.end() + 1000)
                    print(res.text[start:end])
                    print("=" * 60)
        except Exception as e:
            print("Error checking chunk:", e)

if __name__ == '__main__':
    main()
