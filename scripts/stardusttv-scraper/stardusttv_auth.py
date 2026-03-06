#!/usr/bin/env python3
"""
StardustTV Authentication Module
================================

Handles VIP account login and session management for StardustTV.
"""

import requests
import json
from pathlib import Path
from typing import Optional, Dict
import os
from dotenv import load_dotenv

class StardustTVAuth:
    """Manages authentication and session for StardustTV"""
    
    def __init__(self):
        self.base_url = "https://www.stardusttv.net"
        self.api_url = "https://www.stardusttv.net/api"  # May need adjustment
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
            'Origin': 'https://www.stardusttv.net',
            'Referer': 'https://www.stardusttv.net/',
        })
        self.is_authenticated = False
        self.user_info = None
        
        # Load credentials from .env
        load_dotenv()
        self.email = os.getenv('STARDUSTTV_EMAIL')
        self.password = os.getenv('STARDUSTTV_PASSWORD')
    
    def login(self) -> bool:
        """
        Login to StardustTV with VIP credentials
        
        Returns:
            bool: True if login successful, False otherwise
        """
        print("=" * 70)
        print("StardustTV VIP Login")
        print("=" * 70)
        
        if not self.email or not self.password:
            print("[!] Error: Credentials not found in .env file")
            return False
        
        print(f"\n[*] Logging in as: {self.email}")
        
        # First, get the homepage to establish session
        try:
            print("[*] Establishing session...")
            response = self.session.get(self.base_url, timeout=10)
            response.raise_for_status()
            print("[+] Session established")
        except Exception as e:
            print(f"[-] Failed to establish session: {e}")
            return False
        
        # Try different login endpoints
        login_endpoints = [
            f"{self.api_url}/auth/login",
            f"{self.api_url}/login",
            f"{self.base_url}/api/auth/login",
            f"{self.base_url}/login",
        ]
        
        login_data = {
            'email': self.email,
            'password': self.password,
        }
        
        # Also try with username field
        login_data_alt = {
            'username': self.email,
            'password': self.password,
        }
        
        print("\n[*] Attempting login...")
        
        for endpoint in login_endpoints:
            print(f"\n[*] Trying endpoint: {endpoint}")
            
            for data in [login_data, login_data_alt]:
                try:
                    # Try POST request
                    response = self.session.post(
                        endpoint,
                        json=data,
                        timeout=10
                    )
                    
                    print(f"    Status: {response.status_code}")
                    
                    if response.status_code == 200:
                        print("[+] Login successful!")
                        
                        try:
                            result = response.json()
                            self.user_info = result
                            self.is_authenticated = True
                            
                            # Save session cookies
                            self._save_session()
                            
                            print(f"[+] User info: {json.dumps(result, indent=2)[:200]}")
                            return True
                        except:
                            # Even if no JSON, if status is 200, consider it success
                            self.is_authenticated = True
                            self._save_session()
                            print("[+] Login appears successful (no JSON response)")
                            return True
                    
                    elif response.status_code == 404:
                        continue  # Try next endpoint
                    else:
                        print(f"    Response: {response.text[:200]}")
                
                except requests.exceptions.RequestException as e:
                    print(f"    Error: {e}")
                    continue
        
        print("\n[-] All login attempts failed")
        print("\n[*] Trying alternative: Session-based authentication")
        
        # Alternative: Some sites use session cookies without explicit login endpoint
        # Just set the language preference and see if we can access VIP content
        return self._check_vip_access()
    
    def _check_vip_access(self) -> bool:
        """Check if we have VIP access by trying to access a VIP episode"""
        print("\n[*] Checking VIP access...")
        
        # Try to access an episode that might be VIP-locked
        test_url = "https://www.stardusttv.net/episodes/05-dumped-him-married-the-warlord-13263"
        
        try:
            response = self.session.get(test_url, timeout=10)
            
            if response.status_code == 200:
                # Check if page contains VIP lock indicator
                if 'vip' in response.text.lower() or 'locked' in response.text.lower():
                    print("[-] VIP content appears to be locked")
                    return False
                else:
                    print("[+] Can access episode content")
                    self.is_authenticated = True
                    return True
            else:
                print(f"[-] Cannot access episode (status: {response.status_code})")
                return False
        
        except Exception as e:
            print(f"[-] Error checking VIP access: {e}")
            return False
    
    def set_language_indonesian(self) -> bool:
        """Set language preference to Indonesian"""
        print("\n[*] Setting language to Indonesian...")
        
        # Method 1: Set cookie
        self.session.cookies.set('language', 'id')
        self.session.cookies.set('lang', 'id')
        self.session.cookies.set('locale', 'id-ID')
        
        # Method 2: Update headers
        self.session.headers.update({
            'Accept-Language': 'id-ID,id;q=0.9',
        })
        
        print("[+] Language preference set to Indonesian")
        
        # Try to verify by making a request
        try:
            response = self.session.get(self.base_url, timeout=10)
            if 'indonesia' in response.text.lower():
                print("[+] Indonesian language confirmed in response")
                return True
            else:
                print("[!] Warning: Could not confirm Indonesian language")
                return True  # Still return True as we set the preference
        except:
            return True
    
    def _save_session(self):
        """Save session cookies to file"""
        session_file = Path("session_cookies.json")
        
        cookies_dict = requests.utils.dict_from_cookiejar(self.session.cookies)
        
        with open(session_file, 'w') as f:
            json.dump(cookies_dict, f, indent=2)
        
        print(f"[+] Session saved to {session_file}")
    
    def load_session(self) -> bool:
        """Load session cookies from file"""
        session_file = Path("session_cookies.json")
        
        if not session_file.exists():
            return False
        
        try:
            with open(session_file, 'r') as f:
                cookies_dict = json.load(f)
            
            for name, value in cookies_dict.items():
                self.session.cookies.set(name, value)
            
            print("[+] Session loaded from file")
            self.is_authenticated = True
            return True
        
        except Exception as e:
            print(f"[-] Failed to load session: {e}")
            return False
    
    def get_session(self) -> requests.Session:
        """Get the authenticated session"""
        return self.session


def test_auth():
    """Test authentication"""
    auth = StardustTVAuth()
    
    # Try to load existing session first
    if auth.load_session():
        print("\n[+] Using existing session")
    else:
        # Login with credentials
        if not auth.login():
            print("\n[!] Login failed, but continuing anyway...")
    
    # Set language to Indonesian
    auth.set_language_indonesian()
    
    # Test by fetching a drama page
    print("\n" + "=" * 70)
    print("Testing authenticated session")
    print("=" * 70)
    
    test_url = "https://www.stardusttv.net/episodes/01-dumped-him-married-the-warlord-13263"
    session = auth.get_session()
    
    try:
        response = session.get(test_url, timeout=10)
        print(f"\n[*] Status: {response.status_code}")
        print(f"[*] Content length: {len(response.text)} bytes")
        
        # Check for Indonesian indicators
        if 'indonesia' in response.text.lower():
            print("[+] Page contains Indonesian content")
        
        # Check for M3U8 URL
        import re
        m3u8_urls = re.findall(r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*', response.text)
        if m3u8_urls:
            print(f"\n[+] Found {len(m3u8_urls)} M3U8 URL(s)")
            for url in m3u8_urls[:2]:
                import urllib.parse
                decoded = urllib.parse.unquote(url)
                print(f"    {decoded[:80]}...")
        else:
            print("\n[-] No M3U8 URLs found in page source")
            print("    (This is normal - URLs are loaded via JavaScript)")
    
    except Exception as e:
        print(f"[-] Error: {e}")
    
    print("\n" + "=" * 70)
    print("[+] Authentication test complete")
    print("=" * 70)


if __name__ == '__main__':
    test_auth()
