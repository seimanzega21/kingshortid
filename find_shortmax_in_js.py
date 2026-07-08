# -*- coding: utf-8 -*-
import requests, re, urllib3, sys
urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

chunks = [
    '825014a8adcb9585', '123c8307fc6c5765'
]

for chunk in chunks:
    url = f'https://vidrama.asia/_next/static/chunks/{chunk}.js'
    try:
        r = requests.get(url, headers=WEB_HDRS, verify=False)
        if r.ok:
            if 'shortmax' in r.text.lower():
                print(f"\nChunk {chunk}.js contains 'shortmax'!")
                # Find all occurrences
                for match in re.finditer(r'shortmax', r.text, re.IGNORECASE):
                    start = max(0, match.start() - 200)
                    end = min(len(r.text), match.end() + 200)
                    print(f"Match at {match.start()}:")
                    print(r.text[start:end])
                    print("-" * 50)
            else:
                print(f"Chunk {chunk}.js does NOT contain 'shortmax'")
        else:
            print(f"Failed to load chunk {chunk}: {r.status_code}")
    except Exception as e:
        print(f"Error: {e}")
