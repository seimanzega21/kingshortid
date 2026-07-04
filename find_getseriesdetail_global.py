# -*- coding: utf-8 -*-
import requests, re, urllib3, sys
urllib3.disable_warnings()
sys.stdout.reconfigure(encoding='utf-8')

WEB_HDRS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://vidrama.asia/',
}

chunks = [
    '8a450f23ac1062d3', '4ba947795445f824', '111e904f7cf906e0', 'c13d18b2b15b9a28',
    'turbopack-c4c25d99e85ff522', 'a44235986dc198f3', '75b5c11343842a8d', 'd598a6df59c4137a',
    '51333b9c61109047', '54100d0d389c63ef', 'fa58348e1cfbeff8', '85645474589c9371',
    '27d37b3cb4018185', 'b28c44e0f95e3e30', 'b1801931ee7f37d7', '825014a8adcb9585',
    'f45415b48f7fb920', '123c8307fc6c5765', 'a6dad97d9634a72d', 'd94a6b0f5c46d5a7'
]

for chunk in chunks:
    url = f'https://vidrama.asia/_next/static/chunks/{chunk}.js'
    try:
        r = requests.get(url, headers=WEB_HDRS, verify=False)
        if r.ok:
            # We search for getSeriesDetail
            if 'getSeriesDetail' in r.text:
                print(f"Chunk {chunk}.js contains 'getSeriesDetail'!")
                # Print matches and line details
                for match in re.finditer(r'getSeriesDetail', r.text):
                    start = max(0, match.start() - 150)
                    end = min(len(r.text), match.end() + 150)
                    print(f"  Match at {match.start()} in {chunk}.js:")
                    print(r.text[start:end])
                    print("-" * 50)
        else:
            # Maybe chunk is not found
            pass
    except Exception as e:
         print(f"Error reading {chunk}: {e}")
