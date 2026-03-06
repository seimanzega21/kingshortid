#!/usr/bin/env python3
"""
Test different methods to bypass 403 and access StardustTV with Indonesian preference
"""

import requests
import time

def test_access_methods():
    """Test different ways to access StardustTV"""
    
    test_url = "https://www.stardusttv.net/episodes/01-dumped-him-married-the-warlord-13263"
    
    print("="*70)
    print("Testing StardustTV Access Methods")
    print("="*70)
    
    # Method 1: Simple headers (what works in drama_scraper.py)
    print("\n[TEST 1] Simple User-Agent")
    print("-" * 70)
    headers1 = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    try:
        response = requests.get(test_url, headers=headers1, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Content length: {len(response.text)}")
        if response.status_code == 200:
            print("[+] SUCCESS with simple User-Agent!")
        else:
            print(f"[-] Failed: {response.status_code}")
    except Exception as e:
        print(f"[-] Error: {e}")
    
    time.sleep(1)
    
    # Method 2: Full Chrome headers
    print("\n[TEST 2] Full Chrome Headers")
    print("-" * 70)
    headers2 = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0',
    }
    try:
        response = requests.get(test_url, headers=headers2, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Content length: {len(response.text)}")
        if response.status_code == 200:
            print("[+] SUCCESS with full headers!")
        else:
            print(f"[-] Failed: {response.status_code}")
    except Exception as e:
        print(f"[-] Error: {e}")
    
    time.sleep(1)
    
    # Method 3: Session with cookies (Indonesian language)
    print("\n[TEST 3] Session with Indonesian Language Cookies")
    print("-" * 70)
    session = requests.Session()
    session.headers.update(headers1)
    
    # Set Indonesian language cookies
    session.cookies.set('lang', 'id', domain='.stardusttv.net')
    session.cookies.set('language', 'id', domain='.stardusttv.net')
    session.cookies.set('locale', 'id-ID', domain='.stardusttv.net')
    
    try:
        response = session.get(test_url, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Content length: {len(response.text)}")
        if response.status_code == 200:
            print("[+] SUCCESS with session + cookies!")
            
            # Check for Indonesian content
            if 'indonesia' in response.text.lower() or 'bahasa' in response.text.lower():
                print("[+] FOUND Indonesian language indicators!")
            
            # Check for M3U8  
            import re
            m3u8_urls = re.findall(r'https?://[^\s"\'<>]+\.m3u8', response.text)
            if m3u8_urls:
                print(f"[+] Found {len(m3u8_urls)} M3U8 URL(s)")
                for url in m3u8_urls[:2]:
                    import urllib.parse
                    decoded = urllib.parse.unquote(url)
                    print(f"    {decoded[:100]}")
                    
                    # Check language in URL
                    if '印尼' in decoded or '_ID' in decoded.upper() or 'indonesia' in decoded.lower():
                        print("    -> INDONESIAN VERSION DETECTED!")
                    elif '英语' in decoded or '_EN' in decoded.upper():
                        print("    -> English version")
            else:
                print("[-] No M3U8 URLs in HTML (loaded via JavaScript)")
        else:
            print(f"[-] Failed: {response.status_code}")
    except Exception as e:
        print(f"[-] Error: {e}")
    
    print("\n" + "="*70)
    print("Test Complete")
    print("="*70)

if __name__ == '__main__':
    test_access_methods()
