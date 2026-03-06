#!/usr/bin/env python3
"""
Test script to discover language/subtitle information from StardustTV
"""

import requests
from bs4 import BeautifulSoup
import re

def check_drama_languages(drama_url):
    """Check if a drama page has language/subtitle information"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    print(f"Fetching: {drama_url}")
    response = requests.get(drama_url, headers=headers, timeout=10)
    
    soup = BeautifulSoup(response.text, 'html.parser')
    html = response.text
    
    print("\n=== Looking for language indicators ===")
    
    # Check for "Indonesia", "Indonesian", "Bahasa"
    if 'indonesia' in html.lower() or 'bahasa' in html.lower():
        print("[+] Found 'Indonesia' or 'Bahasa' in page")
        # Find context
        matches = re.finditer(r'.{50}(indonesia|bahasa).{50}', html, re.I)
        for i, match in enumerate(matches):
            if i < 3:  # Show first 3 matches
                print(f"  Context: ...{match.group(0)}...")
    else:
        print("[-] No 'Indonesia' or 'Bahasa' found")
    
    # Check for language selector elements
    print("\n=== Checking for language selector ===")
    selectors = soup.find_all(['select', 'button', 'div'], class_=re.compile(r'lang|subtitle|caption', re.I))
    if selectors:
        print(f"[+] Found {len(selectors)} potential language selector elements:")
        for sel in selectors[:5]:
            print(f"  - {sel.name}: {sel.get('class', '')}")
    else:
        print("[-] No obvious language selectors found")
    
    # Check all script tags for language info
    print("\n=== Checking script tags ===")
    scripts = soup.find_all('script')
    for i, script in enumerate(scripts):
        script_text = script.string if script.string else ''
        if 'subtitle' in script_text.lower() or 'language' in script_text.lower() or 'indonesia' in script_text.lower():
            print(f"[+] Script {i+1} contains language/subtitle references")
            # Show snippet
            lines = script_text.split('\n')
            for line in lines:
                if any(word in line.lower() for word in ['subtitle', 'language', 'indonesia', 'caption']):
                    print(f"  {line.strip()[:100]}")
    
    # Check for data attributes
    print("\n=== Checking data attributes ===")
    elements_with_data = soup.find_all(attrs={'data-lang': True})
    elements_with_data += soup.find_all(attrs={'data-language': True})
    elements_with_data += soup.find_all(attrs={'data-subtitle': True})
    if elements_with_data:
        print(f"[+] Found {len(elements_with_data)} elements with language data attributes")
        for elem in elements_with_data[:5]:
            print(f"  - {elem.name}: {elem.attrs}")
    else:
        print("[-] No language data attributes found")
    
    # Extract all M3U8 URLs and analyze paths
    print("\n=== M3U8 URL Analysis ===")
    m3u8_urls = re.findall(r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*', html)
    if m3u8_urls:
        print(f"✓ Found {len(m3u8_urls)} M3U8 URL(s)")
        for url in m3u8_urls[:3]:
            print(f"\n  URL: {url}")
            # Decode URL encoded parts
            import urllib.parse
            decoded = urllib.parse.unquote(url)
            print(f"  Decoded: {decoded}")
            
            # Check for language indicators in path
            if '英语' in decoded or '_EN' in decoded:
                print("  → Language: English")
            elif '印尼' in decoded or 'indonesia' in decoded.lower() or '_ID' in decoded:
                print("  → Language: Indonesian")
            elif '中文' in decoded or '_CN' in decoded or '_ZH' in decoded:
                print("  → Language: Chinese")
    else:
        print("[-] No M3U8 URLs found")
    
    print("\n" + "="*70)

# Test with the two dramas we already scraped
if __name__ == '__main__':
    test_urls = [
        "https://www.stardusttv.net/episodes/01-dumped-him-married-the-warlord-13263",
        "https://www.stardusttv.net/episodes/01-the-billionaire-janitor-13467",
    ]
    
    for url in test_urls:
        print("\n" + "="*70)
        check_drama_languages(url)
        print()
