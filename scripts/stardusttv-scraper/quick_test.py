#!/usr/bin/env python3
"""Quick test to see if basic scraping still works"""

import requests
from bs4 import BeautifulSoup

url = "https://www.stardusttv.net/episodes/01-dumped-him-married-the-warlord-13263"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

print(f"Testing: {url}")
print(f"Headers: {headers}")
print()

try:
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Content-Length: {len(response.text)}")
    
    if response.status_code == 200:
        print("[+] SUCCESS!")
        
        # Check content
        soup = BeautifulSoup(response.text, 'html.parser')
        h1 = soup.find('h1')
        if h1:
            print(f"Title found: {h1.text[:50]}")
    else:
        print(f"[-] FAILED with status {response.status_code}")
        print(f"Response: {response.text[:200]}")

except Exception as e:
    print(f"[-] ERROR: {e}")
