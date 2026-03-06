#!/usr/bin/env python3
"""
StardustTV Selenium Scraper with VIP Authentication
===================================================

Safe, browser-based scraper with:
- VIP account login
- Indonesian language preference
- Rate limiting to prevent account blocking
- M3U8 URL extraction from JavaScript-loaded content
"""

import time
import random
import json
import re
from pathlib import Path
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

class StardustTVSeleniumScraper:
    """Browser automation scraper for StardustTV with Indonesian subtitle support"""
    
    def __init__(self, headless: bool = False):
        """
        Initialize Selenium scraper
        
        Args:
            headless: Run browser in headless mode (invisible)
        """
        self.base_url = "https://www.stardusttv.net"
        self.driver = None
        self.is_logged_in = False
        
        # Load credentials
        load_dotenv()
        self.email = os.getenv('STARDUSTTV_EMAIL')
        self.password = os.getenv('STARDUSTTV_PASSWORD')
        
        # Safety settings
        self.min_delay = 3  # Minimum delay between actions (seconds)
        self.max_delay = 6  # Maximum delay
        
        # Setup Chrome options
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--lang=id-ID')  # Indonesian language
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        self.chrome_options = chrome_options
    
    def start_browser(self):
        """Start Chrome browser"""
        print("[*] Starting Chrome browser...")
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=self.chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("[+] Browser started successfully")
            return True
        
        except Exception as e:
            print(f"[-] Failed to start browser: {e}")
            return False
    
    def safe_delay(self, min_seconds: Optional[float] = None, max_seconds: Optional[float] = None):
        """Random delay to simulate human behavior"""
        min_s = min_seconds or self.min_delay
        max_s = max_seconds or self.max_delay
        delay = random.uniform(min_s, max_s)
        print(f"[*] Waiting {delay:.1f} seconds...")
        time.sleep(delay)
    
    def login(self) -> bool:
        """Login to StardustTV with VIP credentials"""
        print("\n" + "="*70)
        print("StardustTV VIP Login via Browser")
        print("="*70)
        
        if not self.email or not self.password:
            print("[-] No credentials found in .env file")
            return False
        
        try:
            # Go to homepage
            print(f"\n[*] Loading homepage: {self.base_url}")
            self.driver.get(self.base_url)
            self.safe_delay(3, 5)
            
            # Look for login button/link
            print("[*] Looking for login button...")
            
            # Common selectors for login buttons
            login_selectors = [
                "//a[contains(text(), 'Sign In')]",
                "//a[contains(text(), 'Login')]",
                "//button[contains(text(), 'Sign In')]",
                "//button[contains(text(), 'Login')]",
                "//a[contains(@href, 'login')]",
                "//a[contains(@href, 'signin')]",
            ]
            
            login_element = None
            for selector in login_selectors:
                try:
                    login_element = self.driver.find_element(By.XPATH, selector)
                    print(f"[+] Found login element: {selector}")
                    break
                except:
                    continue
            
            if not login_element:
                print("[!] Could not find login button")
                print("[*] Trying to check if already logged in...")
                
                # Check if we see account/profile elements
                if self._check_logged_in():
                    print("[+] Already logged in!")
                    self.is_logged_in = True
                    return True
                
                print("[-] Not logged in and can't find login button")
                print("[*] Saving screenshot for debugging...")
                self.driver.save_screenshot("login_page.png")
                return False
            
            # Click login button
            print("[*] Clicking login button...")
            login_element.click()
            self.safe_delay(2, 4)
            
            # Wait for login form
            print("[*] Waiting for login form...")
            self.safe_delay(2, 3)
            
            # Find email/username field
            print("[*] Looking for email field...")
            email_selectors = [
                "//input[@type='email']",
                "//input[@name='email']",
                "//input[@placeholder*='email']",
                "//input[@placeholder*='Email']",
                "//input[@id='email']",
            ]
            
            email_field = None
            for selector in email_selectors:
                try:
                    email_field = self.driver.find_element(By.XPATH, selector)
                    print(f"[+] Found email field: {selector}")
                    break
                except:
                    continue
            
            if not email_field:
                print("[-] Could not find email field")
                self.driver.save_screenshot("login_form.png")
                return False
            
            # Enter email
            print(f"[*] Entering email: {self.email}")
            email_field.clear()
            email_field.send_keys(self.email)
            self.safe_delay(1, 2)
            
            # Find password field
            print("[*] Looking for password field...")
            password_field = self.driver.find_element(By.XPATH, "//input[@type='password']")
            
            # Enter password
            print("[*] Entering password...")
            password_field.clear()
            password_field.send_keys(self.password)
            self.safe_delay(1, 2)
            
            # Find and click submit button
            print("[*] Looking for submit button...")
            submit_selectors = [
                "//button[@type='submit']",
                "//button[contains(text(), 'Sign In')]",
                "//button[contains(text(), 'Login')]",
                "//input[@type='submit']",
            ]
            
            submit_button = None
            for selector in submit_selectors:
                try:
                    submit_button = self.driver.find_element(By.XPATH, selector)
                    print(f"[+] Found submit button: {selector}")
                    break
                except:
                    continue
            
            if not submit_button:
                print("[-] Could not find submit button")
                return False
            
            # Click submit
            print("[*] Submitting login form...")
            submit_button.click()
            self.safe_delay(4, 6)
            
            # Verify login success
            if self._check_logged_in():
                print("[+] Login successful!")
                self.is_logged_in = True
                return True
            else:
                print("[-] Login may have failed")
                self.driver.save_screenshot("after_login.png")
                return False
        
        except Exception as e:
            print(f"[-] Login error: {e}")
            self.driver.save_screenshot("login_error.png")
            return False
    
    def _check_logged_in(self) -> bool:
        """Check if currently logged in"""
        # Look for indicators of logged-in state
        indicators = [
            "//a[contains(@href, 'profile')]",
            "//a[contains(@href, 'account')]",
            "//button[contains(text(), 'Logout')]",
            "//a[contains(text(), 'Logout')]",
            "//*[contains(text(), 'VIP')]",
        ]
        
        for indicator in indicators:
            try:
                self.driver.find_element(By.XPATH, indicator)
                return True
            except:
                continue
        
        return False
    
    def set_language_indonesian(self) -> bool:
        """Set language to Indonesian (if possible via UI)"""
        print("\n[*] Attempting to set language to Indonesian...")
        
        # StardustTV might auto-detect based on browser lang settings
        # which we set in Chrome options
        print("[+] Language preference set via browser settings (lang=id-ID)")
        return True
    
    def scrape_episode_page(self, url: str) -> Dict:
        """
        Scrape episode page and extract M3U8 URL
        
        Args:
            url: Episode page URL
            
        Returns:
            Dict with episode data including M3U8 URL
        """
        print(f"\n[*] Loading episode: {url}")
        
        try:
            self.driver.get(url)
            self.safe_delay(4, 7)  # Wait for JavaScript to load
            
            data = {}
            
            # Extract title
            try:
                title_element = self.driver.find_element(By.TAG_NAME, "h1")
                data['title'] = title_element.text
                print(f"[+] Title: {data['title'][:50]}...")
            except:
                print("[-] Could not find title")
            
            # Extract description
            try:
                paragraphs = self.driver.find_elements(By.TAG_NAME, "p")
                for p in paragraphs:
                    text = p.text.strip()
                    if len(text) > 50:
                        data['description'] = text
                        print(f"[+] Description: {text[:60]}...")
                        break
            except:
                print("[-] Could not find description")
            
            # Extract M3U8 URL from page source (after JavaScript execution)
            page_source = self.driver.page_source
            
            m3u8_pattern = r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*'
            m3u8_urls = re.findall(m3u8_pattern, page_source)
            
            if m3u8_urls:
                # Get first M3U8 URL
                m3u8_url = m3u8_urls[0]
                data['videoUrl'] = m3u8_url
                
                import urllib.parse
                decoded_url = urllib.parse.unquote(m3u8_url)
                print(f"[+] M3U8 URL found: {decoded_url[:80]}...")
                
                # Check language
                if '印尼' in decoded_url or '_ID' in decoded_url.upper() or 'indonesia' in decoded_url.lower():
                    print("[+] INDONESIAN SUBTITLE DETECTED!")
                    data['language'] = 'indonesian'
                elif '英语' in decoded_url or '_EN' in decoded_url.upper():
                    print("[!] English subtitle detected")
                    data['language'] = 'english'
                else:
                    data['language'] = 'unknown'
            else:
                print("[-] No M3U8 URL found")
                data['videoUrl'] = None
            
            # Extract cover image
            try:
                img = self.driver.find_element(By.TAG_NAME, "img")
                data['coverUrl'] = img.get_attribute('src')
                print(f"[+] Cover URL: {data['coverUrl'][:50]}...")
            except:
                print("[-] Could not find cover image")
            
            return data
        
        except Exception as e:
            print(f"[-] Error scraping episode: {e}")
            return {}
    
    def close(self):
        """Close browser"""
        if self.driver:
            print("\n[*] Closing browser...")
            self.driver.quit()
            print("[+] Browser closed")


def test_selenium_scraper():
    """Test Selenium scraper"""
    print("="*70)
    print("Testing Selenium Scraper")
    print("="*70)
    
    scraper = StardustTVSeleniumScraper(headless=False)  # Visible browser for testing
    
    try:
        # Start browser
        if not scraper.start_browser():
            print("[-] Failed to start browser")
            return
        
        # Login
        if not scraper.login():
            print("[!] Login failed, continuing anyway...")
        
        # Set language
        scraper.set_language_indonesian()
        
        # Test scraping an episode
        test_url = "https://www.stardusttv.net/episodes/01-dumped-him-married-the-warlord-13263"
        episode_data = scraper.scrape_episode_page(test_url)
        
        print("\n" + "="*70)
        print("EXTRACTED DATA:")
        print("="*70)
        print(json.dumps(episode_data, indent=2, ensure_ascii=False))
        
        # Wait a bit to see the results
        print("\n[*] Test complete! Browser will stay open for 10 seconds...")
        time.sleep(10)
    
    finally:
        scraper.close()


if __name__ == '__main__':
    test_selenium_scraper()
